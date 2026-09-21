"""Central Configuration Settings for Fake News Verifier."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------
logger = logging.getLogger("fake_news_verifier")

# ---------------------------------------------------------
# Base Project Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.joblib"
HISTORY_DIR = BASE_DIR / "backend" / "history_logs"

# ---------------------------------------------------------
# Scraper & Whitelist Settings
# ---------------------------------------------------------
# Whitelisted news source keywords used for text matching
ALLOWED_SOURCES = [
    "pti", "press trust of india",
    "uni", "united news of india",
    "pib", "press information bureau",
    "ndtv", "the hindu", "indian express",
    "times of india", "toi", "hindustan times",
    "theprint", "ani", "firstpost", "mid-day", "theweek"
]

# Whitelisted news domain names used directly in Google RSS search operators (site:domain)
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

# RSS & Article Scraper Limits (Configurable via Environment or defaults)
MAX_QUERIES_PER_CLAIM = int(os.getenv("MAX_QUERIES_PER_CLAIM", "2"))
MAX_RSS_ITEMS_PER_QUERY = int(os.getenv("MAX_RSS_ITEMS_PER_QUERY", "12"))
MAX_FALLBACK_ARTICLES = int(os.getenv("MAX_FALLBACK_ARTICLES", "12"))
RSS_REQUEST_TIMEOUT = int(os.getenv("RSS_REQUEST_TIMEOUT", "6"))

# ---------------------------------------------------------
# AI & Pipeline Parameters
# ---------------------------------------------------------
CLAIM_TEXT_TRUNCATE_LEN = 3000
QUERY_PLANNER_PROMPT_LEN = 500

# Fallback list of Gemini models in priority order
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.0-flash",
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]
