"""Central Configuration Settings for Fake News Verifier."""

import logging
import os
from pathlib import Path

import yaml
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
HISTORY_DIR = BASE_DIR / "backend" / "history_logs"

# ---------------------------------------------------------
# Scraper & Whitelist Settings
# ---------------------------------------------------------
SOURCE_TIERS_PATH = Path(__file__).with_name("sources.yaml")
with SOURCE_TIERS_PATH.open("r", encoding="utf-8") as source_file:
    SOURCE_TIERS = yaml.safe_load(source_file) or {}
WHITELISTED_DOMAINS = [domain for domains in SOURCE_TIERS.values() for domain in domains]

# RSS & Article Scraper Limits (Configurable via Environment or defaults)
MAX_QUERIES_PER_CLAIM = int(os.getenv("MAX_QUERIES_PER_CLAIM", "5"))
MAX_RSS_ITEMS_PER_QUERY = int(os.getenv("MAX_RSS_ITEMS_PER_QUERY", "100"))
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "15"))
RSS_REQUEST_TIMEOUT = int(os.getenv("RSS_REQUEST_TIMEOUT", "8"))
MAX_RSS_REQUESTS = int(os.getenv("MAX_RSS_REQUESTS", "10"))

# Per-verification wall-clock budget in seconds
VERIFICATION_TIMEOUT_S = int(os.getenv("VERIFICATION_TIMEOUT_S", "90"))

# ---------------------------------------------------------
# AI & Pipeline Parameters
# ---------------------------------------------------------
CLAIM_TEXT_TRUNCATE_LEN = 3000
QUERY_PLANNER_PROMPT_LEN = 500

# -----------------------------------------------------------------------
# Model lists (real Gemini Developer API model names; validated at startup)
# -----------------------------------------------------------------------
# Planner: up to 3 models in priority order
PLANNER_MODELS: list[str] = [
    m.strip()
    for m in os.getenv(
        "GEMINI_PLANNER_MODELS",
        "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-3.5-flash",
    ).split(",")
    if m.strip()
]

# Analyzer: up to 3 models in priority order
ANALYZER_MODELS: list[str] = [
    m.strip()
    for m in os.getenv(
        "GEMINI_ANALYZER_MODELS",
        "gemini-2.5-flash,gemini-3.5-flash,gemini-2.5-flash-lite",
    ).split(",")
    if m.strip()
]

# Legacy single-model env vars (for backwards compatibility)
PLANNER_MODEL = PLANNER_MODELS[0] if PLANNER_MODELS else "gemini-2.5-flash"
ANALYZER_MODEL = ANALYZER_MODELS[0] if ANALYZER_MODELS else "gemini-2.5-flash"

# Legacy FALLBACK_MODELS for backwards compat (unused in new code path)
FALLBACK_MODELS: list[str] = PLANNER_MODELS[1:] + ANALYZER_MODELS[1:]
