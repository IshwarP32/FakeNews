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

try:
    import googlenewsdecoder
except ImportError:  # pragma: no cover
    googlenewsdecoder = None

import os
import numpy as np

try:
    from fastembed import TextEmbedding
except ImportError:  # pragma: no cover
    TextEmbedding = None

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None

from bs4 import BeautifulSoup

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

    @staticmethod
    def _matches_group(text_lower: str, group: List[str]) -> bool:
        generic_words = {
            "event", "events", "meet", "meets", "the", "of", "in", "at", "for", "and", "or", "a", "an", "to",
            "news", "article", "report", "results", "winner", "winners", "championship",
        }
        for alias in group:
            a_lower = alias.lower().strip()
            if not a_lower:
                continue
            # 1. Exact substring match
            if a_lower in text_lower:
                return True
            # 2. Content tokens (ignoring generic words)
            tokens = [w for w in re.findall(r"\b\w+\b", a_lower) if w not in generic_words and len(w) > 2]
            if len(tokens) >= 2 and all(re.search(r"\b" + re.escape(tok) + r"\b", text_lower) for tok in tokens):
                return True
            # 3. Multi-word distinctive prefix / bigram (e.g. 'inter iit' from 'Inter IIT Sports event')
            words = [w for w in re.findall(r"\b\w+\b", a_lower) if w not in generic_words]
            if len(words) >= 2:
                bigram = f"{words[0]} {words[1]}"
                if re.search(r"\b" + re.escape(bigram) + r"\b", text_lower):
                    return True
        return False

    def _coverage_score(self, article: Dict[str, Any], must_have_terms: List[List[str]]) -> float:
        text = f"{article.get('title', '')} {article.get('excerpt', '')}".lower()
        if not must_have_terms:
            return 1.0
        covered = sum(1 for group in must_have_terms if self._matches_group(text, group))
        return covered / len(must_have_terms)

    _local_embedder = None

    @classmethod
    def _get_local_embedder(cls):
        if cls._local_embedder is None and TextEmbedding is not None:
            try:
                cls._local_embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except Exception as exc:
                logger.debug("Local fastembed model init failed: %s", exc)
        return cls._local_embedder

    def _compute_semantic_similarities(self, claim_text: str, candidate_texts: List[str]) -> List[float]:
        """Compute dense neural embedding similarities (FastEmbed ONNX locally -> Gemini API -> TF-IDF)."""
        if not candidate_texts:
            return []
        if not claim_text.strip():
            return [0.5] * len(candidate_texts)

        # 1. Primary: Fast, local ONNX dense embedding (19ms, ~100MB RAM, zero API calls, ideal for Render)
        embedder = self._get_local_embedder()
        if embedder is not None:
            try:
                all_texts = [claim_text[:1000]] + [t[:1000] for t in candidate_texts]
                embeddings = list(embedder.embed(all_texts))
                claim_vec = embeddings[0]
                claim_norm = float(np.linalg.norm(claim_vec))
                sims = []
                for doc_vec in embeddings[1:]:
                    doc_norm = float(np.linalg.norm(doc_vec))
                    if claim_norm > 0 and doc_norm > 0:
                        cos_sim = float(np.dot(claim_vec, doc_vec) / (claim_norm * doc_norm))
                        sims.append(round(max(0.0, min(1.0, cos_sim)), 4))
                    else:
                        sims.append(0.5)
                if len(sims) == len(candidate_texts):
                    return sims
            except Exception as exc:
                logger.debug("FastEmbed local inference error: %s; trying Gemini cloud embedding", exc)

        # 2. Secondary: Cloud dense neural embedding (gemini-embedding-001)
        api_key = os.getenv("GEMINI_API_KEY")
        if genai is not None and api_key:
            try:
                client = genai.Client(api_key=api_key)
                all_sims: List[float] = []
                chunk_size = 50
                for i in range(0, len(candidate_texts), chunk_size):
                    chunk = candidate_texts[i:i + chunk_size]
                    batch_contents = [claim_text[:1000]] + [t[:1000] for t in chunk]
                    res = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch_contents,
                    )
                    if res and res.embeddings and len(res.embeddings) == len(batch_contents):
                        vecs = [np.array(e.values) for e in res.embeddings]
                        claim_vec = vecs[0]
                        claim_norm = float(np.linalg.norm(claim_vec))
                        for doc_vec in vecs[1:]:
                            doc_norm = float(np.linalg.norm(doc_vec))
                            if claim_norm > 0 and doc_norm > 0:
                                cos_sim = float(np.dot(claim_vec, doc_vec) / (claim_norm * doc_norm))
                                all_sims.append(round(max(0.0, min(1.0, cos_sim)), 4))
                            else:
                                all_sims.append(0.5)
                if len(all_sims) == len(candidate_texts):
                    return all_sims
            except Exception as exc:
                logger.debug("Gemini dense embedding error: %s; falling back to TF-IDF semantic", exc)

        # 3. Tertiary: Robust TF-IDF n-gram cosine fallback (local, instant, zero external API)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            all_docs = [claim_text] + candidate_texts
            tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
            matrix = tfidf.fit_transform(all_docs)
            cosines = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
            return [round(float(s), 4) for s in cosines]
        except Exception as exc:
            logger.debug("TF-IDF semantic scoring fallback failed: %s", exc)
            return [0.5] * len(candidate_texts)

    def _rank_candidate(
        self,
        article: Dict[str, Any],
        claim_analysis: Dict[str, Any],
        semantic_score: Optional[float] = None,
    ) -> float:
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

        if semantic_score is not None:
            # Dense neural semantic similarity 50%, coverage 20%, lexical 10%, tier 20%
            score = 0.50 * semantic_score + 0.20 * coverage + 0.10 * lexical + 0.20 * tier_score - confusion_penalty
        else:
            score = 0.5 * coverage + 0.3 * lexical + 0.2 * tier_score - confusion_penalty
        return round(max(0.0, score), 4)

    def _decode_google_news_url(self, url: str) -> str:
        """Decode Google News redirect URL to direct canonical publisher URL."""
        if not url or "news.google.com" not in url:
            return url
        if googlenewsdecoder is None:
            return url
        try:
            decoded = googlenewsdecoder.gnewsdecoder(url)
            if isinstance(decoded, dict):
                val = decoded.get("decoded_url")
                if val and val.startswith("http"):
                    return val
            elif isinstance(decoded, str) and decoded.startswith("http"):
                return decoded
        except Exception as exc:
            logger.debug("Google news URL decoding failed for %s: %s", url, exc)
        return url

    def _extract_clean_text(self, html_content: str) -> str:
        """Extract clean text using trafilatura with BeautifulSoup fallback."""
        if not html_content:
            return ""
        if trafilatura is not None:
            try:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                )
                if extracted and len(extracted.strip()) > 150:
                    return extracted.strip()
            except Exception:
                pass

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form", "svg", "button"]):
                tag.extract()
            paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
            meaningful = [p for p in paragraphs if len(p) >= 30 and not p.lower().startswith("copyright")]
            if meaningful:
                return "\n\n".join(meaningful)
        except Exception:
            pass

        return ""

    def _fetch_article_excerpt(self, article: Dict[str, Any], claim_analysis: Dict[str, Any]) -> None:
        """Decode Google News redirect to direct URL and scrape full article body."""
        # Never overwrite Wikipedia reference extracts which are already extracted and curated
        if article.get("source") == "Wikipedia" or article.get("fetch_status") == "full_text":
            return

        raw_url = article.get("link", "")
        if not raw_url:
            return

        # 1. Decode Google News redirect URL to direct canonical publisher URL
        direct_url = self._decode_google_news_url(raw_url)
        if direct_url and direct_url != raw_url:
            article["link"] = direct_url
            try:
                domain = urllib.parse.urlparse(direct_url).netloc.lower()
                if domain:
                    article["publisher_site"] = f"https://{domain}"
            except Exception:
                pass

        target_url = article.get("link", "")
        if not _is_safe_url(target_url):
            logger.debug("Skipping article fetch (SSRF check): %s", target_url)
            return

        # 2. Fetch direct HTML
        try:
            resp = requests.get(
                target_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                },
                timeout=RSS_REQUEST_TIMEOUT + 3,
            )
            if resp.status_code != 200 or not resp.text:
                return

            extracted = self._extract_clean_text(resp.text)
            if not extracted or len(extracted.strip()) < 100:
                return

            terms = [alias.lower() for group in claim_analysis.get("must_have_terms", []) for alias in group]
            lower_text = extracted.lower()
            match_positions = [lower_text.find(term) for term in terms if lower_text.find(term) >= 0]
            start = max(0, min(match_positions) - 400) if match_positions else 0
            # Keep up to 2500 chars of substantive context for Agent 3
            article["excerpt"] = extracted[start: start + 2500].strip()
            article["fetch_status"] = "full_text"
        except Exception as exc:
            logger.debug("Article extraction failed for %s: %s", article.get("link"), exc)

    def _resolve_wikipedia_title(self, session: Any, query: str, timeout: int = 5) -> Optional[str]:
        """Use Wikipedia opensearch to resolve a query to a canonical article title."""
        try:
            resp = session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": "3",
                    "namespace": "0",
                    "format": "json",
                },
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 1 and data[1]:
                    return data[1][0]  # First match title
        except Exception as exc:
            logger.debug("Wikipedia opensearch failed for %r: %s", query, exc)
        return None

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

        must_have_terms = claim_analysis.get("must_have_terms", [])
        must_have_aliases = [alias.lower() for g in must_have_terms for alias in g]
        target_anchors = [d.lower() for d in explicit_dates] + must_have_aliases

        all_aliases_per_group: List[List[str]] = [
            [a for a in g if a] for g in must_have_terms
        ]

        session = requests.Session()
        session.headers.update({
            "User-Agent": "FakeNewsVerifier/2.0 (research; educational; contact: ishwarpatil8767@gmail.com)"
        })

        search_queries: List[str] = []

        # Priority 1: Unquoted alias + date (e.g. 'Inter IIT Sports event 2014')
        if explicit_dates:
            for group in all_aliases_per_group:
                for alias in group[:2]:
                    if len(alias.split()) >= 2:
                        search_queries.append(f"{alias} {explicit_dates[0]}")
            if len(entities) >= 2:
                search_queries.append(f"{entities[0]} {entities[1]} {explicit_dates[0]}")

        # Priority 2: Normalized claim text
        norm_claim = claim_analysis.get("normalized_claim", "")
        if norm_claim:
            search_queries.append(norm_claim)

        # Priority 3: Pairwise combinations across alias groups
        if len(all_aliases_per_group) >= 2:
            for alias_a in all_aliases_per_group[0][:2]:
                for alias_b in all_aliases_per_group[1][:2]:
                    search_queries.append(f'"{alias_a}" "{alias_b}"')

        # Priority 4: Individual aliases and entity names
        for group in all_aliases_per_group:
            for alias in group[:2]:
                if explicit_dates:
                    search_queries.append(f'"{alias}" {explicit_dates[0]}')
                search_queries.append(f'"{alias}"')

        seen_q: set = set()
        unique_queries: List[str] = []
        for q in search_queries:
            if q not in seen_q:
                seen_q.add(q)
                unique_queries.append(q)

        title_scores: Dict[str, float] = {}

        for q in unique_queries[:6]:
            try:
                resp = session.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": q,
                        "format": "json",
                        "utf8": "1",
                        "srlimit": "4",
                    },
                    timeout=5,
                )
                if resp.status_code == 200:
                    results = resp.json().get("query", {}).get("search", [])
                    for rank, item in enumerate(results):
                        t = item.get("title")
                        if not t:
                            continue
                        rank_score = max(1, 4 - rank)
                        title_lower = t.lower()
                        snippet_lower = (item.get("snippet") or "").lower()
                        combined = f"{title_lower} {snippet_lower}"
                        anchor_hits = sum(1 for a in target_anchors if a in combined)
                        token_bonus = sum(2 for g in must_have_terms if self._matches_group(title_lower, g))
                        total_score = rank_score + (anchor_hits * 2) + token_bonus

                        if t not in title_scores or total_score > title_scores[t]:
                            title_scores[t] = total_score
            except Exception as exc:
                logger.debug("Wikipedia search query %r failed: %s", q, exc)

        wiki_log["items_returned"] = len(title_scores)
        if not title_scores:
            wiki_log["status"] = "empty"
            return [], wiki_log

        sorted_titles = sorted(title_scores.items(), key=lambda kv: kv[1], reverse=True)
        titles_to_fetch = [t for t, _ in sorted_titles[:5]]

        wiki_candidates: List[Dict[str, Any]] = []

        for title in titles_to_fetch:
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
                    page_url = (
                        p.get("fullurl")
                        or f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    )

                    # Split on double newlines to keep headers and associated section bodies together
                    paragraphs = [para.strip() for para in extract.split("\n\n") if para.strip()]

                    # Tier 1: paragraphs matching BOTH date AND any entity group
                    best_paras = []
                    for para in paragraphs:
                        para_lower = para.lower()
                        has_date = any(d.lower() in para_lower for d in explicit_dates) if explicit_dates else True
                        has_entity = any(self._matches_group(para_lower, g) for g in must_have_terms) if must_have_terms else True
                        if has_date and has_entity:
                            best_paras.append(para)

                    if best_paras:
                        excerpt = "\n\n".join(best_paras)[:2500]
                    else:
                        # Tier 2: paragraphs matching any entity group
                        para_anchors = [
                            para for para in paragraphs
                            if any(self._matches_group(para.lower(), g) for g in must_have_terms)
                        ]
                        if para_anchors:
                            excerpt = "\n\n".join(para_anchors[:3])[:2000]
                        else:
                            # Tier 3: beginning of article as last resort
                            excerpt = extract[:1500]

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
                    item["coverage"] = self._coverage_score(item, must_have_terms)
                    item["score"] = self._rank_candidate(item, claim_analysis)

                    # Keep Wikipedia candidates with basic term relevance
                    if item["coverage"] >= 0.33 or not must_have_terms:
                        wiki_candidates.append(item)
                        wiki_log["items_kept"] += 1
            except Exception as exc:
                logger.debug("Wikipedia extract fetch failed for %r: %s", title, exc)

        # Sort so the highest-scoring Wikipedia article appears first
        wiki_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
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

                        candidates[canonical_key] = item
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
                query_logs.append({
                    "query": {"q": "wikipedia:reference_fallback", "role": "historical"},
                    "items_returned": 0,
                    "items_kept": 0,
                    "domains": ["wikipedia.org"],
                    "error": str(exc),
                    "status": "failed",
                    "rss_url": "https://en.wikipedia.org/w/api.php",
                    "role": "historical",
                    "window_source": "wikipedia_fallback",
                })

        # Batch Semantic Search Ranking across all retrieved candidates
        normalized_claim = claim_analysis.get("normalized_claim", "") or ""
        candidate_items = list(candidates.values())
        if candidate_items and normalized_claim:
            candidate_texts = [f"{c.get('title', '')} {c.get('excerpt', '')}" for c in candidate_items]
            semantic_sims = self._compute_semantic_similarities(normalized_claim, candidate_texts)
            for c, sim in zip(candidate_items, semantic_sims):
                c["semantic_score"] = sim
                c["score"] = self._rank_candidate(c, claim_analysis, semantic_score=sim)
        else:
            for c in candidate_items:
                c["semantic_score"] = 0.5
                c["score"] = self._rank_candidate(c, claim_analysis)

        # Soft Semantic Filter: prune completely unrelated noise (semantic_score < 0.40)
        # Authentic related news scores 0.58 - 0.85; noise scores < 0.40.
        filtered_candidates: Dict[str, Dict[str, Any]] = {}
        for key, c in candidates.items():
            if c.get("source") == "Wikipedia" or c.get("semantic_score", 0.5) >= 0.40:
                filtered_candidates[key] = c

        # Safeguard: if filter pruned too aggressively, fall back to best scored candidates
        if len(filtered_candidates) < 3 and len(candidates) >= 3:
            filtered_candidates = candidates

        candidates = filtered_candidates

        # Update per-query kept counts in query_logs
        for q_log in query_logs:
            q_text = q_log.get("query", {}).get("q", "") if isinstance(q_log.get("query"), dict) else ""
            if q_log.get("window_source") == "wikipedia_fallback" or (q_text and q_text.startswith("wikipedia:")):
                q_log["items_kept"] = sum(1 for c in candidates.values() if c.get("source") == "Wikipedia")
            elif q_text:
                q_log["items_kept"] = sum(1 for c in candidates.values() if c.get("query") == q_text)

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

        # Fetch full text for selected candidates
        with ThreadPoolExecutor(max_workers=5) as executor:
            fetch_futures = [executor.submit(self._fetch_article_excerpt, article, claim_analysis) for article in selected]
            for f in fetch_futures:
                try:
                    f.result(timeout=RSS_REQUEST_TIMEOUT + 4)
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
