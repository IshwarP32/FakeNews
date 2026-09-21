"""Agent 1: Search Query Planner."""

import json
import re
from datetime import datetime
from typing import List, Optional
from backend.config import logger
from backend.utils.progress import ProgressCallback, report


class QueryPlannerAgent:
    """Agent 1 generates targeted search queries for Indian news sources."""

    def plan_queries(self, claim: str, gemini_caller, on_progress: Optional[ProgressCallback] = None) -> List[str]:
        report(on_progress, "query_planning", "Agent 1 (Query Planner): Generating search queries...")
        logger.info("Agent 1: Planning search queries...")

        current_year = datetime.now().year
        prompt = (
            f'Generate 2 targeted search queries for Indian news sources to verify this claim: "{claim[:500]}". '
            f'Ensure queries focus on finding the latest news reports (year {current_year}). '
            'Return ONLY a JSON array of strings, e.g. ["query1", "query2"]'
        )
        try:
            resp, _ = gemini_caller(prompt, use_search=False, on_progress=on_progress)
            text = getattr(resp, "text", "") or ""
            text = text.replace("```json", "").replace("```", "").strip()
            queries = json.loads(text)
            if isinstance(queries, list) and queries:
                return [str(q) for q in queries[:3]]
        except Exception as e:
            logger.warning(f"Query planning fallback triggered: {e}")

        words = [w for w in re.findall(r"\w+", claim) if len(w) > 3][:5]
        return [" ".join(words) + f" India news {current_year}"]
