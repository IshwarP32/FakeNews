"""History Logging Service for Fake News Verifier."""

import json
import os
import re
from datetime import datetime
from backend.config import HISTORY_DIR, logger


def save_history_log(claim: str, queries: list, articles: list, verdict: dict) -> str:
    """Saves query execution details to a timestamped JSON file in HISTORY_DIR."""
    try:
        os.makedirs(HISTORY_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_slug = re.sub(r"\W+", "_", claim[:30]).strip("_").lower() or "query"
        filename = f"{timestamp}_{safe_slug}.json"
        filepath = os.path.join(HISTORY_DIR, filename)

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_claim": claim,
            "agent1_planned_queries": queries,
            "agent2_scraped_articles": articles,
            "agent3_final_verdict": verdict,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Query history saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to save history log: {e}")
        return ""
