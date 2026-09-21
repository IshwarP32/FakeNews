"""Configuration settings and environment loading for Fake News Verifier."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Logger Setup
logger = logging.getLogger("fake_news_verifier")

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.joblib"
HISTORY_DIR = BASE_DIR / "backend" / "history_logs"

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
