"""Agent 2: Live News Scraper (Restricted to Whitelisted Outlets & Date Prioritized)."""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple
from backend.config import logger
from backend.utils.progress import ProgressCallback, report

# Whitelist of trusted Indian news agencies and outlets
ALLOWED_SOURCES = [
    "pti", "press trust of india",
    "uni", "united news of india",
    "pib", "press information bureau",
    "ndtv", "the hindu", "indian express",
    "times of india", "toi", "hindustan times",
    "theprint", "ani", "firstpost", "mid-day", "theweek"
]

WHITELISTED_DOMAINS = [
    "ndtv.com",
    "thehindu.com",
    "indianexpress.com",
    "timesofindia.indiatimes.com",
    "hindustantimes.com",
    "pib.gov.in",
    "theprint.in",
    "firstpost.com",
    "mid-day.com",
    "theweek.in"
]


class NewsScraperAgent:
    """Agent 2 searches and scrapes RSS feeds for specific trusted Indian news sources."""

    def is_whitelisted_source(self, source_name: str, title: str) -> bool:
        """Checks if the article source or title matches our trusted outlets list."""
        text = f"{source_name} {title}".lower()
        return any(allowed in text for allowed in ALLOWED_SOURCES)

    def _parse_pub_date(self, date_str: str) -> datetime:
        """Parses RSS pubDate string to datetime for date sorting."""
        if not date_str:
            return datetime.min
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            return datetime.min

    def _fetch_rss_items(self, query: str) -> Tuple[str, List[Dict[str, str]]]:
        """Executes HTTP request to Google News RSS and returns parsed items."""
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            root = ET.fromstring(resp.read())

        items = []
        for item in root.findall(".//item")[:6]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source = (item.findtext("source") or "News Agency").strip()
            raw_pub_date = (item.findtext("pubDate") or "").strip()
            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "pubDate": raw_pub_date
                })
        return url, items

    def scrape_news(
        self, queries: List[str], on_progress: Optional[ProgressCallback] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        report(on_progress, "web_scraping", f"Agent 2 (News Scraper): Scraping whitelisted news RSS feeds for {len(queries)} queries...")
        logger.info(f"Agent 2: Scraping restricted news RSS for queries: {queries}")

        site_filter_operator = " OR ".join([f"site:{d}" for d in WHITELISTED_DOMAINS])

        articles = []
        fallback_articles = []
        seen_titles = set()
        queries_log = []

        for base_q in queries:
            query_log = {
                "base_query": base_q,
                "whitelisted_site_filter_applied": True,
                "rss_url": "",
                "raw_rss_items_count": 0,
                "raw_rss_items": [],
                "whitelisted_matches": [],
                "fallback_matches": [],
                "error": None
            }

            # Pass 1: Targeted search applying site: filters directly in Google RSS query
            targeted_q = f"{base_q} ({site_filter_operator})"
            fetched_items = []
            try:
                url, fetched_items = self._fetch_rss_items(targeted_q)
                query_log["rss_url"] = url
            except Exception as e:
                logger.warning(f"Whitelisted RSS search failed for '{targeted_q}': {e}")
                query_log["error"] = str(e)

            # Pass 2: Fallback to general RSS search if targeted site filter returned 0 items
            if not fetched_items:
                try:
                    query_log["whitelisted_site_filter_applied"] = False
                    url, fetched_items = self._fetch_rss_items(base_q)
                    query_log["rss_url"] = url
                except Exception as e:
                    query_log["error"] = str(e)
                    logger.warning(f"Fallback RSS search failed for '{base_q}': {e}")

            query_log["raw_rss_items_count"] = len(fetched_items)
            query_log["raw_rss_items"] = fetched_items

            for raw_item in fetched_items:
                title = raw_item["title"]
                link = raw_item["link"]
                source = raw_item["source"]
                raw_pub_date = raw_item["pubDate"]

                if title and title not in seen_titles:
                    seen_titles.add(title)
                    dt = self._parse_pub_date(raw_pub_date)
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M") if dt != datetime.min else raw_pub_date

                    article_data = {
                        "title": title,
                        "link": link,
                        "source": source,
                        "pub_date": formatted_date or "Recent",
                        "_datetime": dt
                    }

                    if self.is_whitelisted_source(source, title) or query_log["whitelisted_site_filter_applied"]:
                        articles.append(article_data)
                        query_log["whitelisted_matches"].append(title)
                    else:
                        fallback_articles.append(article_data)
                        query_log["fallback_matches"].append(title)

            queries_log.append(query_log)

        candidates = articles if articles else fallback_articles[:6]
        # Sort candidates chronologically (most recent news articles first)
        candidates.sort(key=lambda a: a.get("_datetime", datetime.min), reverse=True)

        # Remove internal datetime sort key before returning
        final_articles = []
        for a in candidates:
            cleaned = {k: v for k, v in a.items() if k != "_datetime"}
            final_articles.append(cleaned)

        scraper_log = {
            "queries_processed": queries_log,
            "total_raw_items_fetched": sum(q.get("raw_rss_items_count", 0) for q in queries_log),
            "total_whitelisted_articles": len(articles),
            "final_selected_articles": final_articles
        }

        report(on_progress, "articles_found", f"Agent 2: Gathered {len(final_articles)} date-prioritized whitelisted articles.")
        return final_articles, scraper_log
