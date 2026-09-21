"""Agent 1: Search Query Planner."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from backend.config import logger
from backend.utils.progress import ProgressCallback, report


class QueryPlannerAgent:
    """Agent 1 generates targeted search queries for Indian news sources."""

    def plan_queries(self, claim: str, gemini_caller, on_progress: Optional[ProgressCallback] = None) -> Tuple[List[str], Dict[str, Any]]:
        report(on_progress, "query_planning", "Agent 1 (Query Planner): Generating search queries...")
        logger.info("Agent 1: Planning search queries...")

        current_year = datetime.now().year
        prompt = (
            f'Generate 2 targeted search queries for Indian news sources to verify this claim: "{claim[:500]}". '
            f'Ensure queries focus on finding the latest news reports (year {current_year}). '
            'Return ONLY a JSON array of strings, e.g. ["query1", "query2"]'
        )
        raw_response_text = ""
        queries = []

        try:
            resp, _ = gemini_caller(prompt, use_search=False, on_progress=on_progress)
            raw_response_text = getattr(resp, "text", "") or ""
            cleaned_text = raw_response_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, list) and parsed:
                queries = [str(q) for q in parsed[:3]]
        except Exception as e:
            logger.warning(f"Query planning fallback triggered: {e}")

        if not queries:
            words = [w for w in re.findall(r"\w+", claim) if len(w) > 3][:5]
            queries = [" ".join(words) + f" India news {current_year}"]

        planner_log = {
            "prompt_sent": prompt,
            "raw_gemini_response": raw_response_text,
            "planned_queries": queries,
        }

        return queries, planner_log
