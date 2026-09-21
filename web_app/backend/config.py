"""Configuration and fallback settings for Fake News Verifier."""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Setup Logger
logger = logging.getLogger("fake_news_verifier")

# Model fallback list in priority order requested by user
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
