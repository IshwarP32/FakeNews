"""Main Gemini Verifier Pipeline Orchestrator."""

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from backend.agents.analyzer import EvidenceAnalyzerAgent
from backend.agents.planner import QueryPlannerAgent
from backend.agents.scraper import NewsScraperAgent
from backend.config import CLAIM_TEXT_TRUNCATE_LEN, FALLBACK_MODELS, logger
from backend.services.history import save_history_log
from backend.utils.progress import ProgressCallback, report


class GeminiVerifier:
    """Orchestrates Agent 1 (Planner), Agent 2 (Scraper), and Agent 3 (Analyzer)."""

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.search_tool = types.Tool(google_search=types.GoogleSearch())
        self.planner = QueryPlannerAgent()
        self.scraper = NewsScraperAgent()
        self.analyzer = EvidenceAnalyzerAgent()

    def _call_gemini(self, prompt: str, use_search: bool = False, on_progress: Optional[ProgressCallback] = None):
        """Executes Gemini calls using the 10-model fallback chain."""
        models = [os.getenv("GEMINI_MODEL")] if os.getenv("GEMINI_MODEL") else []
        for m in FALLBACK_MODELS:
            if m not in models:
                models.append(m)

        config = {"temperature": 0}
        if use_search:
            config["tools"] = [self.search_tool]

        last_err = None
        for model in models:
            for attempt in range(2):
                try:
                    logger.info(f"Calling Gemini model: {model} (attempt {attempt + 1})")
                    resp = self.client.models.generate_content(
                        model=model, contents=prompt, config=types.GenerateContentConfig(**config)
                    )
                    return resp, model
                except Exception as e:
                    last_err = e
                    logger.warning(f"Model {model} failed: {e}")
                    if any(x in str(e).lower() for x in ["404", "not found", "invalid"]):
                        break
                    time.sleep(2)
            report(on_progress, "model_fallback", f"{model} unavailable. Trying next fallback model...")

        logger.error("All fallback models failed.")
        raise last_err or RuntimeError("All models failed")

    def verify(self, title: str = "", text: str = "", on_progress: Optional[ProgressCallback] = None) -> Dict[str, Any]:
        claim = " ".join(f"{title} {text}".split())
        if not claim:
            return {"verdict": "Unverified", "confidence": "Low", "summary": "Empty claim provided.", "sources_used": []}

        logger.info(f"Starting verification pipeline for claim: {claim[:80]}...")
        report(on_progress, "analysis_started", "Starting verification pipeline...")

        # Step 1: Agent 1 - Search Query Planner
        queries, planner_log = self.planner.plan_queries(claim, self._call_gemini, on_progress)

        # Step 2: Agent 2 - Live News Scraper (Date Prioritized & Detailed RSS Logging)
        articles, scraper_log = self.scraper.scrape_news(queries, on_progress)

        # Build date-aware evidence prompt for Agent 3
        evidence = ""
        if articles:
            evidence_lines = [
                f"- [Published: {a.get('pub_date', 'Recent')}] {a['title']} (Source: {a['source']})"
                for a in articles
            ]
            evidence = "SCRAPED NEWS EVIDENCE (Ordered by Publication Date - Latest First):\n" + "\n".join(evidence_lines)

        today_str = datetime.now().strftime("%B %d, %Y")

        report(on_progress, "analyzing_evidence", "Agent 3 (Evidence Analyzer): Evaluating claim & news timestamps...")
        prompt = f"""You are a professional news fact-checker. Today's date is {today_str}.

Verify this claim: "{claim[:CLAIM_TEXT_TRUNCATE_LEN]}"

{evidence}

STRICT DATE & TEMPORAL EVALUATION RULES:
1. Pay STRICT attention to publication dates of news articles versus the claim.
2. Prioritize recent news articles over outdated ones.
3. Check if an OLD event (e.g., past rainfall, old accident, past statement from prior months/years) is being re-circulated or misrepresented as CURRENT news today.
4. Explicitly evaluate the temporal relevance in your explanation and reasoning.

Return JSON strictly in this format:
{{
  "verdict": "True|False|Partially True|Unverified",
  "confidence": "High|Medium|Low",
  "summary": "2 sentence explanation with explicit date context",
  "corrected_news": "actual verified facts including accurate dates",
  "reasoning": ["reason 1 (must analyze dates & source freshness)", "reason 2"],
  "date_analysis": "Clear assessment of news freshness, publication dates, and whether this claim matches current events or is recycled old news",
  "sources_used": ["source 1", "source 2"]
}}"""

        # Step 3: Agent 3 - Evidence Analysis
        use_search = len(articles) == 0
        resp, model_used = self._call_gemini(prompt, use_search=use_search, on_progress=on_progress)
        raw_text = self.analyzer.extract_text(resp)
        result = self.analyzer.parse_json(raw_text)

        analyzer_log = {
            "prompt_sent": prompt,
            "model_used": model_used,
            "used_fallback_google_search": use_search,
            "raw_gemini_response": raw_text,
            "parsed_result": result,
        }

        # Attach ALL article source links with direct publisher URL and pub_date
        sources = []
        for a in articles:
            sources.append({
                "title": f"{a['title']} - {a['source']}",
                "url": a["link"],
                "publisher_site": a.get("publisher_site", ""),
                "pub_date": a.get("pub_date", "")
            })
        result["grounding_sources"] = sources

        # Save complete query history log with raw RSS and Gemini telemetry
        save_history_log(
            claim=claim,
            title=title,
            text=text,
            planner_log=planner_log,
            scraper_log=scraper_log,
            analyzer_log=analyzer_log,
            verdict=result,
        )

        logger.info(f"Verification complete: {result.get('verdict')} using model {model_used}")
        report(
            on_progress,
            "verification_completed",
            f"Verdict: {result.get('verdict')} ({result.get('confidence')} confidence)",
            verdict=result
        )
        return result
