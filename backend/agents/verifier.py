"""Main Gemini Verifier Pipeline Orchestrator.

Phase 1+5+6+8 improvements:
- Uses LLMClient (error classification, cooldown, capability table)
- Zero-article short-circuit in Agent 3 (no Gemini call)
- Wall-clock budget
- Per-run telemetry trace
- No tools for Agent 3 (asserted)
- claim_analysis sent as JSON (not Python repr)
- Coverage block with per-window status and retrieval_incomplete
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.agents.analyzer import EvidenceAnalyzerAgent
from backend.agents.planner import QueryPlannerAgent
from backend.agents.scraper import NewsScraperAgent
from backend.config import (
    ANALYZER_MODELS,
    MAX_RSS_REQUESTS,
    PLANNER_MODELS,
    VERIFICATION_TIMEOUT_S,
    logger,
)
from backend.config.prompts import (
    EVIDENCE_ANALYZER_SYSTEM_INSTRUCTION,
    build_evidence_analysis_prompt,
)
from backend.llm_client import LLMClient
from backend.schemas.verification import EvidenceAnalysis
from backend.services.history import save_history_log
from backend.utils.progress import ProgressCallback, report


class GeminiVerifier:
    """Orchestrates Agent 1 (Planner), Agent 2 (Scraper), and Agent 3 (Analyzer)."""

    def __init__(self):
        self.llm_client = LLMClient()
        self.planner = QueryPlannerAgent()
        self.scraper = NewsScraperAgent()
        self.analyzer = EvidenceAnalyzerAgent()

    def verify(self, title: str = "", text: str = "", on_progress: Optional[ProgressCallback] = None) -> Dict[str, Any]:
        claim = " ".join(f"{title} {text}".split())
        if not claim:
            return {
                "schema_version": "2.0",
                "verdict": {
                    "verdict": "Unverified",
                    "confidence": "Low",
                    "summary": "Empty claim provided.",
                    "limitations": "A headline or article text is required.",
                    "flags": [],
                },
                "evidence_articles": [],
                "context_articles": [],
                "coverage": {},
            }

        logger.info("Starting verification pipeline for claim: %s...", claim[:80])
        report(on_progress, "analysis_started", "Starting verification pipeline...")

        wall_clock_start = time.monotonic()
        wall_clock_deadline = wall_clock_start + VERIFICATION_TIMEOUT_S

        trace: Dict[str, Any] = {
            "claim": claim,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "planner_log": None,
            "scraper_log": None,
            "analyzer_log": None,
        }

        try:
            local_zone = ZoneInfo("Asia/Kolkata")
        except ZoneInfoNotFoundError:
            local_zone = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(local_zone).date().isoformat()

        # -----------------------------------------------------------------
        # Step 1: Agent 1 - Query Planner
        # -----------------------------------------------------------------
        try:
            queries, planner_log = self.planner.plan_queries(
                claim=claim,
                llm_client=self.llm_client,
                models=PLANNER_MODELS,
                on_progress=on_progress,
                max_rss_requests=MAX_RSS_REQUESTS,
            )
            trace["planner_log"] = planner_log
        except Exception as exc:
            err_msg = str(exc)
            logger.error("Agent 1 failed: %s", err_msg)
            if "llm_config_error" in err_msg:
                reason_code = "llm_config_error"
            elif "llm_quota_exhausted" in err_msg:
                reason_code = "llm_quota_exhausted"
            else:
                reason_code = "llm_unavailable"
            return self._error_result(reason_code, err_msg)

        claim_analysis = planner_log.get("claim_analysis", {"normalized_claim": claim})

        # -----------------------------------------------------------------
        # Step 2: Agent 2 - News Scraper
        # -----------------------------------------------------------------
        articles, scraper_log = self.scraper.scrape_news(
            queries,
            claim_analysis=claim_analysis,
            on_progress=on_progress,
        )
        trace["scraper_log"] = {"query_count": len(queries), "articles_found": len(articles)}

        # -----------------------------------------------------------------
        # Step 3: Agent 3 - Evidence Analysis
        # -----------------------------------------------------------------
        report(on_progress, "analyzing_evidence", "Agent 3 (Evidence Analyzer): Evaluating claim & article relevance...")

        # Build coverage dict to pass to Agent 3
        query_logs = scraper_log.get("queries_processed", [])
        coverage_for_agent3 = {
            "queries_searched": len(query_logs),
            "retrieval_incomplete": scraper_log.get("retrieval_incomplete", False),
            "windows": [
                {
                    "role": log.get("role", ""),
                    "after": log.get("after"),
                    "before": log.get("before"),
                    "status": log.get("status", "ok"),
                    "items_kept": log.get("items_kept", 0),
                    "error": log.get("error"),
                }
                for log in query_logs
            ],
        }

        # ZERO-ARTICLE SHORT-CIRCUIT: never call Gemini with zero articles
        if not articles:
            logger.info("Zero articles retrieved; returning deterministic Unverified without Gemini call")
            result = self.analyzer.build_zero_article_result(claim_analysis, scraper_log)
            model_used = "none (zero-article short-circuit)"
            raw_text = ""
        else:
            # ASSERT: no tools in Agent 3 call (Phase 3 rule 1, invariant)
            # LLMClient.generate() never adds tools - this is structural, not a flag
            self.llm_client.assert_no_tools_in_analyzer_call()

            prompt = build_evidence_analysis_prompt(
                today_str,
                claim_analysis,
                articles,
                coverage=coverage_for_agent3,
            )

            raw_text = ""
            result = None
            try:
                resp, model_used = self.llm_client.generate(
                    models=ANALYZER_MODELS,
                    prompt=prompt,
                    system_instruction=EVIDENCE_ANALYZER_SYSTEM_INSTRUCTION,
                    response_schema=EvidenceAnalysis,
                    thinking_level="medium",
                    wall_clock_deadline=wall_clock_deadline,
                )
                raw_text = self.analyzer.extract_text(resp)
                result = self.analyzer.parse_json(raw_text)

                # Retry once on validation failure
                if result.get("verdict") == "Unverified" and not result.get("article_assessments") and articles:
                    logger.info("Agent 3 returned empty assessments; retrying once")
                    resp2, model_used = self.llm_client.generate(
                        models=ANALYZER_MODELS,
                        prompt=prompt,
                        system_instruction=EVIDENCE_ANALYZER_SYSTEM_INSTRUCTION,
                        response_schema=EvidenceAnalysis,
                        thinking_level="medium",
                        wall_clock_deadline=wall_clock_deadline,
                        retry_prompt_suffix="Please assess every provided article and populate article_assessments.",
                    )
                    raw_text = self.analyzer.extract_text(resp2)
                    result = self.analyzer.parse_json(raw_text)

            except Exception as exc:
                err_msg = str(exc)
                logger.error("Agent 3 failed: %s", err_msg)
                if "llm_config_error" in err_msg:
                    return self._error_result("llm_config_error", err_msg, failed_agent="Agent 3 (Evidence Analyzer)")
                elif "llm_quota_exhausted" in err_msg:
                    return self._error_result("llm_quota_exhausted", err_msg, failed_agent="Agent 3 (Evidence Analyzer)")
                elif "wall-clock budget" in err_msg:
                    return self._error_result("llm_timeout", "Verification exceeded time budget. Please retry.", failed_agent="Agent 3 (Evidence Analyzer)")
                return self._error_result("llm_unavailable", f"Evidence analysis failed: {err_msg[:200]}", failed_agent="Agent 3 (Evidence Analyzer)")

        # Validate and ground the result
        result = self.analyzer.validate_grounding(result, articles)

        # -----------------------------------------------------------------
        # Build response
        # -----------------------------------------------------------------
        article_by_id = {article.get("id"): article for article in articles}
        evidence_articles: List[Dict[str, Any]] = []
        context_articles: List[Dict[str, Any]] = []

        for assessment in result.get("article_assessments", []):
            article = article_by_id.get(assessment.get("id"))
            if not article:
                continue
            if assessment.get("relevance") == "irrelevant":
                continue  # Never return irrelevant articles to frontend
            article_view = {
                **article,
                "relevance": assessment.get("relevance"),
                "stance": assessment.get("stance"),
                "evidence_quote": assessment.get("evidence_quote"),
                "event_date": assessment.get("event_date", {}),
                "article_kind": assessment.get("article_kind", "unclear"),
                "near_miss_entity": assessment.get("near_miss_entity"),
                "applies_to_reading": assessment.get("applies_to_reading", "neither"),
            }
            if assessment.get("relevance") == "direct" and assessment.get("stance") in {"supports", "contradicts"}:
                evidence_articles.append(article_view)
            elif assessment.get("relevance") == "contextual" or (
                assessment.get("relevance") == "direct" and assessment.get("stance") == "neutral_context"
            ):
                context_articles.append(article_view)

        # Code-side verdict consistency check (Phase 6.2 - already done in validate_grounding)
        # Additional: ensure verdict is not True/False if no direct evidence in final list
        direct_ids = {a.get("id") for a in evidence_articles}
        if result.get("verdict") in {"True", "False", "Partially True", "Misleading"} and not direct_ids:
            result["verdict"] = "Unverified"
            result["confidence"] = "Low"
            result["flags"] = sorted(set(result.get("flags", [])) | {"no_direct_evidence"})
            result["limitations"] = "No validated direct evidence supported the primary reading."

        # Confidence capping: unknown sources alone can't support High
        independent_sources_with_tier = {
            article.get("publisher_site") or article.get("source")
            for article in evidence_articles
            if article.get("source_tier") != "unknown"
        }
        if len(independent_sources_with_tier) < 2 and result.get("confidence") == "High":
            result["confidence"] = "Medium"

        # -----------------------------------------------------------------
        # Coverage block
        # -----------------------------------------------------------------
        independent_sources_all = {article.get("publisher_site") or article.get("source") for article in evidence_articles}
        pub_dates = sorted(a.get("pub_date", "") for a in articles if a.get("pub_date"))

        coverage = {
            "queries_run": len(queries),
            "windows": [
                {
                    "role": log.get("role", ""),
                    "after": log.get("after"),
                    "before": log.get("before"),
                    "status": log.get("status", "ok"),
                    "items_returned": log.get("items_returned", 0),
                    "items_kept": log.get("items_kept", 0),
                    "error": log.get("error"),
                    "rss_url": log.get("rss_url", ""),
                    "purpose": log.get("query", {}).get("purpose", ""),
                }
                for log in query_logs
            ],
            "articles_retrieved": scraper_log.get("total_raw_items_fetched", 0),
            "articles_ranked": len(articles),
            "articles_analysed": len(result.get("article_assessments", [])),
            "independent_sources": len(independent_sources_all),
            "date_range": {
                "earliest_publication": pub_dates[0] if pub_dates else None,
                "latest_publication": pub_dates[-1] if pub_dates else None,
            },
            "empty_pools": [pool for pool, count in scraper_log.get("pool_counts", {}).items() if count == 0],
            "retrieval_incomplete": scraper_log.get("retrieval_incomplete", False),
        }

        # Check for pipeline errors in retrieval
        pipeline_error = None
        if not articles and scraper_log.get("retrieval_incomplete", False):
            failed_count = sum(1 for q in query_logs if q.get("status") == "failed")
            pipeline_error = {
                "reason_code": "retrieval_failed",
                "message": (
                    f"News retrieval error: {failed_count} of {len(query_logs)} search queries encountered errors "
                    "(connection/timeout). No articles could be fetched."
                ),
                "guidance": "Please verify internet connection and retry. News endpoints may be temporarily unreachable.",
                "failed_agent": "Agent 2 (News Scraper)",
            }

        # -----------------------------------------------------------------
        # Telemetry log
        # -----------------------------------------------------------------
        analyzer_log = {
            "model_used": model_used,
            "raw_gemini_response": raw_text,
            "parsed_result": result,
            "article_count_sent": len(articles),
            "zero_article_short_circuit": not articles,
        }
        trace["analyzer_log"] = {"model_used": model_used, "verdict": result.get("verdict")}

        save_history_log(
            claim=claim,
            title=title,
            text=text,
            planner_log=planner_log,
            scraper_log=scraper_log,
            analyzer_log=analyzer_log,
            verdict=result,
        )

        logger.info(
            "Verification complete: %s (%s) using model %s. Evidence: %d, Context: %d",
            result.get("verdict"), result.get("confidence"), model_used,
            len(evidence_articles), len(context_articles),
        )
        report(
            on_progress,
            "verification_completed",
            f"Verdict: {result.get('verdict')} ({result.get('confidence')} confidence)",
            verdict=result,
        )
        return {
            "schema_version": "2.0",
            "error": pipeline_error,
            "verdict": result,
            "evidence_articles": evidence_articles,
            "context_articles": context_articles,
            "coverage": coverage,
        }

    def _error_result(self, reason_code: str, message: str, failed_agent: str = "Agent 1 (Query Planner)") -> Dict[str, Any]:
        """Return a structured error state (never an invented verdict)."""
        logger.error("Pipeline error in %s: %s - %s", failed_agent, reason_code, message)
        guidance = {
            "llm_config_error": "A configuration error occurred. Please contact support.",
            "llm_quota_exhausted": "API quota exceeded across all configured models. Please retry in a few minutes or add fallback keys.",
            "llm_unavailable": "The AI service is temporarily unavailable across all models. Please retry.",
            "llm_timeout": "Analysis exceeded the time budget. Please retry.",
            "retrieval_failed": "Network/retrieval error: Unable to connect to news sources. Please verify internet connectivity.",
        }.get(reason_code, "An unexpected error occurred. Please retry.")
        return {
            "schema_version": "2.0",
            "error": {
                "reason_code": reason_code,
                "message": message,
                "guidance": guidance,
                "failed_agent": failed_agent,
            },
            "verdict": None,
            "evidence_articles": [],
            "context_articles": [],
            "coverage": {},
        }
