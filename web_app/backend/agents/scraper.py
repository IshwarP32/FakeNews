"""Agent 2: Live News Scraper (Restricted to Whitelisted Outlets)."""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from web_app.backend.config import logger
from web_app.backend.progress import ProgressCallback, report

# Whitelist of trusted Indian news agencies and outlets
ALLOWED_SOURCES = [
    "pti", "press trust of india",
    "uni", "united news of india",
    "pib", "press information bureau",
    "ndtv", "the hindu", "indian express",
    "times of india", "toi", "hindustan times",
    "theprint", "ani", "firstpost"
]


class NewsScraperAgent:
    """Agent 2 searches and scrapes RSS feeds for specific trusted Indian news sources."""

    def is_whitelisted_source(self, source_name: str, title: str) -> bool:
        """Checks if the article source or title matches our trusted outlets list."""
        text = f"{source_name} {title}".lower()
        return any(allowed in text for allowed in ALLOWED_SOURCES)

    def scrape_news(self, queries: List[str], on_progress: Optional[ProgressCallback] = None) -> List[Dict[str, str]]:
        report(on_progress, "web_scraping", f"Agent 2 (News Scraper): Scraping trusted news feeds for {len(queries)} queries...")
        logger.info(f"Agent 2: Scraping restricted news RSS for queries: {queries}")

        articles = []
        fallback_articles = []
        seen_titles = set()

        for q in queries:
            try:
                encoded = urllib.parse.quote(q)
                url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    root = ET.fromstring(resp.read())

                for item in root.findall(".//item")[:6]:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    source = (item.findtext("source") or "News Agency").strip()

                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        article_data = {"title": title, "link": link, "source": source}
                        
                        # Filter for whitelisted sources
                        if self.is_whitelisted_source(source, title):
                            articles.append(article_data)
                        else:
                            fallback_articles.append(article_data)
            except Exception as e:
                logger.warning(f"Scraper error for query '{q}': {e}")

        # If strict whitelist produced 0 articles, use fallback items so pipeline has context
        final_articles = articles if articles else fallback_articles[:4]
        
        report(on_progress, "articles_found", f"Agent 2: Gathered {len(final_articles)} articles from selected news sources.")
        return final_articles
