"""History Logging Service for Fake News Verifier."""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.config import HISTORY_DIR, logger


def save_history_log(
    claim: str,
    title: str = "",
    text: str = "",
    planner_log: Optional[Dict[str, Any]] = None,
    scraper_log: Optional[Dict[str, Any]] = None,
    analyzer_log: Optional[Dict[str, Any]] = None,
    verdict: Optional[Dict[str, Any]] = None,
) -> str:
    """Saves detailed query execution telemetry and raw RSS/Gemini requests to HISTORY_DIR."""
    try:
        os.makedirs(HISTORY_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_slug = re.sub(r"\W+", "_", (claim or title)[:30]).strip("_").lower() or "query"
        filename = f"{timestamp}_{safe_slug}.json"
        filepath = os.path.join(HISTORY_DIR, filename)

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_request": {
                "claim": claim,
                "title": title,
                "text": text,
            },
            "pipeline_telemetry": {
                "agent1_query_planner": planner_log or {},
                "agent2_news_scraper": scraper_log or {},
                "agent3_evidence_analyzer": analyzer_log or {},
            },
            "final_verdict": verdict or {},
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Query history telemetry saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to save history log: {e}")
        return ""
