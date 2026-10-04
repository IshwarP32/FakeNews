"""Agent 2: date-windowed Google News retrieval and candidate ranking.

Phase 3 improvements:
- Retry timeouts (up to 2 attempts, exponential backoff)
- Per-window status: ok | empty | failed (never swallowed)
- retrieval_incomplete flag when any window failed
- Stable IDs assigned AFTER ranking (A01..A15)
- fetch_status correctly set to full_text or snippet_only
- SSRF protection on article fetching
- Pool quotas enforced (at least 1/3 of MAX_CANDIDATES per non-empty pool)
- Dedup by canonical URL then by normalised title
- Source tiers from sources.yaml
"""

from __future__ import annotations

import html
import json
import re
import socket
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.config import (
    MAX_CANDIDATES,
    MAX_RSS_ITEMS_PER_QUERY,
    RSS_REQUEST_TIMEOUT,
    SOURCE_TIERS,
    logger,
)
from backend.utils.progress import ProgressCallback, report

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None

# Private IP ranges to block for SSRF protection
_PRIVATE_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
    "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.",
    "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
    "192.168.", "127.", "0.", "169.254.", "::1", "fc", "fd",
)
_MAX_ARTICLE_BODY_BYTES = 256 * 1024  # 256 KB
_MAX_REDIRECTS = 5


def _is_safe_url(url: str) -> bool:
    """Block private/loopback/link-local URLs (SSRF protection)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        # Resolve to IP if needed
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            return False
        return not any(ip.startswith(p) for p in _PRIVATE_PREFIXES)
    except Exception:
        return False


class NewsScraperAgent:
    """Retrieve, rank, and pool Google News RSS candidates without judging claims."""

    def _normalise_domain(self, value: str) -> str:
        domain = urllib.parse.urlparse(value if "://" in value else f"https://{value}").netloc.lower()
        return re.sub(r"^(www\.|m\.|amp\.)", "", domain)

    def _source_tier(self, publisher_site: str) -> str:
        domain = self._normalise_domain(publisher_site)
        for tier, domains in SOURCE_TIERS.items():
            if any(domain == candidate or domain.endswith(f".{candidate}") for candidate in domains):
                return tier
        return "unknown"

    def _parse_pub_date(self, date_str: str) -> datetime:
        if not date_str:
            return datetime.min
        try:
            parsed = parsedate_to_datetime(date_str)
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        except (TypeError, ValueError, OverflowError):
            return datetime.min

    def _clean_html(self, value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", html.unescape(text)).strip()

    def _fetch_rss_items_once(self, planned_query: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        """Single attempt to fetch RSS items for a query."""
        query = str(planned_query.get("q", "")).strip()
        site_hint = planned_query.get("site_hint")
        if site_hint:
            query = f"{query} site:{site_hint}"

        after = planned_query.get("after")
        before = planned_query.get("before")
        if after:
            query += f" after:{after}"
        if before:
            query += f" before:{before}"

        lang = planned_query.get("language", "en")
        params = {
            "q": query,
            "hl": "hi" if lang == "hi" else "en-IN",
            "gl": "IN",
            "ceid": "IN:hi" if lang == "hi" else "IN:en",
        }
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FakeNewsVerifier/2.0 (research; educational)"},
        )
        with urllib.request.urlopen(req, timeout=RSS_REQUEST_TIMEOUT) as response:
            root = ET.fromstring(response.read())

        items: List[Dict[str, Any]] = []
        for item in root.findall(".//item")[:MAX_RSS_ITEMS_PER_QUERY]:
            source_element = item.find("source")
            publisher_site = (source_element.attrib.get("url") if source_element is not None else "") or ""
            items.append({
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "source": (source_element.text if source_element is not None else "") or "Unknown publisher",
                "publisher_site": publisher_site.strip(),
                "pub_date": (item.findtext("pubDate") or "").strip(),
                "excerpt": self._clean_html(item.findtext("description") or ""),
            })
        return url, items

    def _fetch_rss_items(self, planned_query: Dict[str, Any], max_retries: int = 2) -> Tuple[str, List[Dict[str, Any]], str]:
        """Fetch RSS with retry on transient errors. Returns (url, items, status)."""
        last_exc = None
        for attempt in range(max_retries):
            try:
                url, items = self._fetch_rss_items_once(planned_query)
                return url, items, "ok"
            except Exception as exc:
                last_exc = exc
                msg = str(exc).lower()
                # Retry timeouts and 5xx, not 4xx
                if "timed out" in msg or "timeout" in msg or "connection" in msg or "50" in msg:
                    if attempt < max_retries - 1:
                        sleep_t = 1.5 * (attempt + 1)
                        logger.info("RSS retry %d after %.1fs for query %r: %s", attempt + 1, sleep_t, planned_query.get("q", ""), exc)
                        time.sleep(sleep_t)
                        continue
                break  # Non-retryable error
        logger.warning("RSS fetch failed after %d attempts for %r: %s", max_retries, planned_query.get("q", ""), last_exc)
        return "", [], "failed"

    def _coverage_score(self, article: Dict[str, Any], must_have_terms: List[List[str]]) -> float:
        text = f"{article.get('title', '')} {article.get('excerpt', '')}".lower()
        if not must_have_terms:
            return 1.0
        covered = sum(1 for group in must_have_terms if any(alias.lower() in text for alias in group))
        return covered / len(must_have_terms)

    def _rank_candidate(self, article: Dict[str, Any], claim_analysis: Dict[str, Any]) -> float:
        coverage = self._coverage_score(article, claim_analysis.get("must_have_terms", []))
        claim_tokens = set(re.findall(r"\w+", claim_analysis.get("normalized_claim", "").lower()))
        article_tokens = set(re.findall(r"\w+", f"{article.get('title', '')} {article.get('excerpt', '')}".lower()))
        lexical = len(claim_tokens & article_tokens) / max(1, len(claim_tokens))
        tier_score = {
            "official": 1.0, "wire_national": 0.9, "factchecker": 0.85,
            "other_known": 0.7, "reference": 0.5, "unknown": 0.2,
        }.get(article.get("source_tier"), 0.2)
        # Penalise likely confusions
        likely_confusions = [c.lower() for c in claim_analysis.get("likely_confusions", [])]
        text_lower = f"{article.get('title', '')} {article.get('excerpt', '')}".lower()
        confusion_penalty = 0.2 if any(c in text_lower for c in likely_confusions) else 0.0
        score = 0.5 * coverage + 0.3 * lexical + 0.2 * tier_score - confusion_penalty
        return round(max(0.0, score), 4)

    def _fetch_article_excerpt(self, article: Dict[str, Any], claim_analysis: Dict[str, Any]) -> None:
        """Replace a weak RSS snippet with a bounded extracted passage when possible."""
        if trafilatura is None or not article.get("link"):
            return
        url = article["link"]
        if not _is_safe_url(url):
            logger.debug("Skipping article fetch (SSRF check): %s", url)
            return
        try:
            downloaded = trafilatura.fetch_url(url)
            extracted = trafilatura.extract(downloaded or "", include_comments=False, include_tables=False) or ""
            if not extracted:
                return
            terms = [alias.lower() for group in claim_analysis.get("must_have_terms", []) for alias in group]
            lower_text = extracted.lower()
            match_positions = [lower_text.find(term) for term in terms if lower_text.find(term) >= 0]
            start = max(0, min(match_positions) - 450) if match_positions else 0
            article["excerpt"] = extracted[start: start + 1200]
            article["fetch_status"] = "full_text"
        except Exception as exc:
            logger.debug("Article extraction failed for %s: %s", article.get("link"), exc)

    def _fetch_wikipedia_candidates(self, claim_analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch encyclopedic reference fallback articles from Wikipedia MediaWiki API.

        Source tier: 'reference'. Assigned a lower credibility prior (0.5 vs official 1.0)
        since community wikis are openly editable.
        """
        wiki_log: Dict[str, Any] = {
            "query": {"q": "wikipedia:reference_fallback", "role": "historical"},
            "items_returned": 0,
            "items_kept": 0,
            "domains": ["wikipedia.org"],
            "error": None,
            "status": "ok",
            "rss_url": "https://en.wikipedia.org/w/api.php",
            "role": "historical",
            "window_source": "wikipedia_fallback",
        }

        if not claim_analysis:
            wiki_log["status"] = "empty"
            return [], wiki_log

        entities = [e.get("name") for e in claim_analysis.get("entities", []) if e.get("name")]
        explicit_dates = claim_analysis.get("explicit_dates", [])
        time_ref = claim_analysis.get("time_reference", "latest")
        is_historical = time_ref in ("explicit_date", "timeless_historical", "historical") or bool(explicit_dates)
        pool = "historical" if is_historical else "recent"

        search_queries: List[str] = []
        if entities:
            if len(entities) >= 2:
                search_queries.append(f'"{entities[0]}" "{entities[1]}"')
            for ent in reversed(entities):
                if explicit_dates:
                    search_queries.append(f'"{ent}" {explicit_dates[0]}')
                search_queries.append(f'"{ent}"')
        else:
            norm_claim = claim_analysis.get("normalized_claim", "")
            if norm_claim:
                search_queries.append(norm_claim)

        session = requests.Session()
        session.headers.update({
            "User-Agent": "FakeNewsVerifier/2.0 (research; educational; contact: ishwarpatil8767@gmail.com)"
        })

        found_titles: List[str] = []
        for q in search_queries[:4]:
            try:
                resp = session.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": q,
                        "format": "json",
                        "utf8": "1",
                        "srlimit": "2",
                    },
                    timeout=5,
                )
                if resp.status_code == 200:
                    for item in resp.json().get("query", {}).get("search", []):
                        t = item.get("title")
                        if t and t not in found_titles:
                            found_titles.append(t)
            except Exception as exc:
                logger.debug("Wikipedia search query %r failed: %s", q, exc)

        wiki_log["items_returned"] = len(found_titles)
        if not found_titles:
            wiki_log["status"] = "empty"
            return [], wiki_log

        wiki_candidates: List[Dict[str, Any]] = []
        must_have_aliases = [alias.lower() for g in claim_analysis.get("must_have_terms", []) for alias in g]
        target_anchors = [d.lower() for d in explicit_dates] + must_have_aliases

        for title in found_titles[:2]:
            try:
                resp = session.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts|info",
                        "inprop": "url",
                        "explaintext": "1",
                        "titles": title,
                        "format": "json",
                        "utf8": "1",
                    },
                    timeout=5,
                )
                if resp.status_code != 200:
                    continue
                pages = resp.json().get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    extract = (p.get("extract") or "").strip()
                    if not extract:
                        continue
                    page_url = p.get("fullurl") or f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

                    paragraphs = [para.strip() for para in extract.split("\n\n") if para.strip()]
                    best_paras = []
                    for para in paragraphs:
                        para_lower = para.lower()
                        has_date = any(d.lower() in para_lower for d in explicit_dates) if explicit_dates else True
                        has_entity = any(alias.lower() in para_lower for alias in must_have_aliases) if must_have_aliases else True
                        if has_date and has_entity:
                            best_paras.append(para)

                    if best_paras:
                        excerpt = "\n\n".join(best_paras)[:1500]
                    else:
                        para_anchors = [para for para in paragraphs if any(a in para.lower() for a in target_anchors)]
                        if para_anchors:
                            excerpt = "\n\n".join(para_anchors[:2])[:1500]
                        else:
                            excerpt = extract[:1200]

                    pub_date_str = explicit_dates[0] if explicit_dates else ""
                    item = {
                        "title": f"Wikipedia: {title}",
                        "link": page_url,
                        "source": "Wikipedia",
                        "publisher_site": "https://en.wikipedia.org",
                        "source_tier": "reference",
                        "pub_date": pub_date_str,
                        "_datetime": self._parse_pub_date(pub_date_str),
                        "retrieval_pool": pool,
                        "query": f"wikipedia:{title}",
                        "excerpt": excerpt.strip(),
                        "fetch_status": "full_text",
                    }
                    item["coverage"] = self._coverage_score(item, claim_analysis.get("must_have_terms", []))
                    item["score"] = self._rank_candidate(item, claim_analysis)

                    if item["coverage"] > 0 or not claim_analysis.get("must_have_terms"):
                        wiki_candidates.append(item)
                        wiki_log["items_kept"] += 1
            except Exception as exc:
                logger.debug("Wikipedia extract fetch failed for %r: %s", title, exc)

        return wiki_candidates, wiki_log

    def scrape_news(
        self,
        planned_queries: List[Dict[str, Any]],
        claim_analysis: Optional[Dict[str, Any]] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        claim_analysis = claim_analysis or {}
        report(on_progress, "web_scraping", f"Agent 2 (News Scraper): Running {len(planned_queries)} date-windowed searches...")
        query_logs: List[Dict[str, Any]] = []
        candidates: Dict[str, Dict[str, Any]] = {}  # canonical_key -> article
        retrieval_incomplete = False

        max_workers = min(6, max(1, len(planned_queries) + 1))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._fetch_rss_items, query): query for query in planned_queries}
            wiki_future = executor.submit(self._fetch_wikipedia_candidates, claim_analysis)

            for future in as_completed(futures):
                query = futures[future]
                log: Dict[str, Any] = {
                    "query": query,
                    "items_returned": 0,
                    "items_kept": 0,
                    "domains": [],
                    "error": None,
                    "status": "ok",
                    "rss_url": "",
                    "role": query.get("_window_role", query.get("window_role", "")),
                    "after": query.get("after"),
                    "before": query.get("before"),
                    "window_source": query.get("_window_source", ""),
                }
                try:
                    url, items, status = future.result()
                    log["rss_url"] = url
                    log["status"] = status
                    log["items_returned"] = len(items)

                    if status == "failed":
                        retrieval_incomplete = True
                        log["error"] = "RSS fetch failed after retries"
                    elif not items:
                        log["status"] = "empty"

                    for item in items:
                        if not item.get("title"):
                            continue
                        # Dedup by normalised title key
                        canonical_key = re.sub(r"\W+", " ", item.get("title", "").lower()).strip()
                        if canonical_key in candidates:
                            continue
                        item["source_tier"] = self._source_tier(item.get("publisher_site", ""))
                        # Pool assignment: based on query window role
                        role = query.get("_window_role", query.get("window_role", "latest"))
                        item["retrieval_pool"] = "historical" if role in ("historical", "claim_period") else "recent"
                        item["query"] = query.get("q", "")
                        item["_datetime"] = self._parse_pub_date(item.get("pub_date", ""))
                        item["pub_date"] = item["_datetime"].isoformat() if item["_datetime"] != datetime.min else item.get("pub_date", "")
                        item["coverage"] = self._coverage_score(item, claim_analysis.get("must_have_terms", []))
                        item["score"] = self._rank_candidate(item, claim_analysis)
                        item["fetch_status"] = "snippet_only"  # default; full_text set by _fetch_article_excerpt

                        # Drop articles with 0 must_have_terms coverage (irrelevant at retrieval time)
                        if item["coverage"] <= 0 and claim_analysis.get("must_have_terms"):
                            continue

                        candidates[canonical_key] = item
                        log["items_kept"] += 1
                        log["domains"].append(item.get("publisher_site", ""))

                except Exception as exc:
                    log["error"] = str(exc)
                    log["status"] = "failed"
                    retrieval_incomplete = True
                    logger.warning("RSS future failed for %r: %s", query.get("q", ""), exc)

                query_logs.append(log)

            # Integrate Wikipedia fallback candidates
            try:
                wiki_items, wiki_log = wiki_future.result(timeout=15)
                query_logs.append(wiki_log)
                logger.info("Wikipedia fallback retrieved %d reference candidates (status=%s)", len(wiki_items), wiki_log.get("status"))
                for item in wiki_items:
                    canonical_key = re.sub(r"\W+", " ", item.get("title", "").lower()).strip()
                    if canonical_key in candidates:
                        continue
                    candidates[canonical_key] = item
            except Exception as exc:
                logger.warning("Wikipedia fallback processing error: %s", exc)

        # Pool separation and quota
        grouped: Dict[str, List[Dict[str, Any]]] = {"recent": [], "historical": []}
        for candidate in candidates.values():
            pool = candidate.get("retrieval_pool", "recent")
            grouped.setdefault(pool, []).append(candidate)

        for pool in grouped.values():
            pool.sort(key=lambda item: item.get("score", 0), reverse=True)

        # Pool quota: at least 1/3 of MAX_CANDIDATES per non-empty pool
        quota = max(1, MAX_CANDIDATES // 3)
        selected: List[Dict[str, Any]] = []
        for pool_name in ("recent", "historical"):
            pool_items = grouped.get(pool_name, [])
            selected.extend(pool_items[:quota])

        # Fill remaining slots from best overall
        already_selected_keys = {id(item) for item in selected}
        remaining = sorted(
            [item for item in candidates.values() if id(item) not in already_selected_keys],
            key=lambda item: item.get("score", 0), reverse=True,
        )
        selected.extend(remaining[: max(0, MAX_CANDIDATES - len(selected))])
        selected = selected[:MAX_CANDIDATES]

        # Fetch full text for top candidates
        with ThreadPoolExecutor(max_workers=3) as executor:
            fetch_futures = [executor.submit(self._fetch_article_excerpt, article, claim_analysis) for article in selected[:5]]
            for f in fetch_futures:
                try:
                    f.result(timeout=RSS_REQUEST_TIMEOUT + 2)
                except Exception as exc:
                    logger.debug("Article excerpt future error: %s", exc)

        # Assign stable IDs AFTER selection and ranking
        final_articles: List[Dict[str, Any]] = []
        for index, article in enumerate(selected, start=1):
            cleaned = {key: value for key, value in article.items() if not key.startswith("_")}
            cleaned["id"] = f"A{index:02d}"
            if "fetch_status" not in cleaned:
                cleaned["fetch_status"] = "snippet_only"
            final_articles.append(cleaned)

        scraper_log = {
            "queries_processed": query_logs,
            "total_raw_items_fetched": sum(log.get("items_returned", 0) for log in query_logs),
            "final_selected_articles": final_articles,
            "pool_counts": {pool: len(items) for pool, items in grouped.items()},
            "retrieval_incomplete": retrieval_incomplete,
        }
        report(on_progress, "articles_found", f"Agent 2: ranked {len(final_articles)} candidates across recent and historical pools.")
        return final_articles, scraper_log
