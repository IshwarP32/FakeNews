"""Main Gemini Verifier Pipeline Orchestrator."""

import os
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from web_app.backend.agents.analyzer import EvidenceAnalyzerAgent
from web_app.backend.agents.planner import QueryPlannerAgent
from web_app.backend.agents.scraper import NewsScraperAgent
from web_app.backend.config import FALLBACK_MODELS, logger
from web_app.backend.history import save_history_log
from web_app.backend.progress import ProgressCallback, report


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
        queries = self.planner.plan_queries(claim, self._call_gemini, on_progress)

        # Step 2: Agent 2 - Live News Scraper
        articles = self.scraper.scrape_news(queries, on_progress)

        # Build evidence prompt for Agent 3
        evidence = ""
        if articles:
            evidence = "SCRAPED NEWS EVIDENCE:\n" + "\n".join(
                [f"- {a['title']} (Source: {a['source']})" for a in articles]
            )

        report(on_progress, "analyzing_evidence", "Agent 3 (Evidence Analyzer): Evaluating claim...")
        prompt = f"""You are a news fact-checker. Verify this claim: "{claim[:3000]}"

{evidence}

Return JSON strictly in this format:
{{
  "verdict": "True|False|Partially True|Unverified",
  "confidence": "High|Medium|Low",
  "summary": "2 sentence explanation",
  "corrected_news": "actual facts",
  "reasoning": ["reason 1", "reason 2"],
  "sources_used": ["source 1", "source 2"]
}}"""

        # Step 3: Agent 3 - Evidence Analysis
        use_search = len(articles) == 0
        resp, model_used = self._call_gemini(prompt, use_search=use_search, on_progress=on_progress)
        raw_text = self.analyzer.extract_text(resp)
        result = self.analyzer.parse_json(raw_text)

        # Attach article source links
        sources = []
        for a in articles:
            sources.append({"title": f"{a['title']} - {a['source']}", "url": a["link"]})
        result["grounding_sources"] = sources

        # Save history log to history_logs/ directory
        save_history_log(claim, queries, articles, result)

        logger.info(f"Verification complete: {result.get('verdict')} using model {model_used}")
        report(
            on_progress,
            "verification_completed",
            f"Verdict: {result.get('verdict')} ({result.get('confidence')} confidence)",
            verdict=result
        )
        return result
