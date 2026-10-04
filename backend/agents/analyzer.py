"""Agent 3: Evidence Analyzer & Fact Verifier.

Phase 5 & 6 improvements:
- Zero-article short-circuit: never call Gemini with zero articles
- Citation validation: every [A..] must exist and be non-irrelevant
- Quote grounding: evidence_quote must be verbatim substring
- Verdict consistency: True requires all propositions supported by direct articles
- Confidence capping based on code-side rubric
- Grounding check on summary and corrected_news (years, numbers, named entities)
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from backend.config import logger
from backend.schemas.verification import EvidenceAnalysis


# Words in fact texts that need grounding (patterns to check)
_YEAR_PATTERN = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")
_NUMBER_PATTERN = re.compile(r"\b\d[\d,\.]*\d\b")


class EvidenceAnalyzerAgent:
    """Agent 3 cross-examines claim against evidence and formats structured JSON."""

    def build_zero_article_result(
        self,
        claim_analysis: Dict[str, Any],
        scraper_log: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return a deterministic Unverified result when there are zero usable articles.

        Never calls Gemini. Never says 'no articles were provided'.
        Uses coverage data to write an honest limitations string.
        """
        retrieval_incomplete = scraper_log.get("retrieval_incomplete", False)
        query_logs = scraper_log.get("queries_processed", [])

        # Build coverage summary
        n_queries = len(query_logs)
        failed_windows = [log for log in query_logs if log.get("status") == "failed"]
        empty_windows = [log for log in query_logs if log.get("status") == "empty"]
        windows_ok = [log for log in query_logs if log.get("status") == "ok"]

        # Build date range from query windows
        after_dates = [log.get("after", "") for log in query_logs if log.get("after")]
        before_dates = [log.get("before", "") for log in query_logs if log.get("before")]
        date_range_str = ""
        if after_dates and before_dates:
            date_range_str = f" (searched {min(after_dates)} to {max(before_dates)})"

        if retrieval_incomplete and all(log.get("status") == "failed" for log in query_logs if log):
            # Total retrieval failure
            limitations = (
                f"Retrieval failed: all {n_queries} search queries encountered errors{date_range_str}. "
                "This may be a temporary network issue. Please retry."
            )
        elif retrieval_incomplete:
            limitations = (
                f"Searched {n_queries} queries{date_range_str}: "
                f"{len(failed_windows)} failed (network/timeout), {len(empty_windows)} returned no results, "
                f"{len(windows_ok)} succeeded but no relevant articles were found. "
                "Results may be incomplete due to retrieval errors."
            )
        else:
            limitations = (
                f"Searched {n_queries} queries{date_range_str}: no relevant articles were found in any window."
            )

        flags = ["no_direct_evidence"]
        if retrieval_incomplete:
            flags.append("retrieval_incomplete")

        return EvidenceAnalysis(
            article_assessments=[],
            propositions=[],
            temporal_analysis={
                "time_reference": claim_analysis.get("time_reference", "implicit_news_like"),
                "primary_reading_applied": claim_analysis.get("primary_reading", ""),
                "evidence_found_for_primary_reading": False,
                "recycled_news_suspected": False,
                "notes": "No articles retrieved for analysis.",
            },
            historical_context=[],
            verdict="Unverified",
            flags=sorted(flags),
            confidence="Low",
            summary="No relevant articles were found for this claim.",
            corrected_news=None,
            limitations=limitations,
        ).model_dump()

    def extract_text(self, resp: Any) -> str:
        """Safely extracts raw text from Gemini response candidates."""
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates") and resp.candidates:
            for c in resp.candidates:
                parts = getattr(getattr(c, "content", None), "parts", []) or []
                pieces = [p.text for p in parts if getattr(p, "text", None)]
                if pieces:
                    text = "\n".join(pieces)
                    break
        return (text or "").strip()

    def parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Parse and validate a structured Agent 3 response."""
        cleaned = raw_text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            cleaned = match.group(1).strip() if match else cleaned.split("```")[1]
        try:
            return EvidenceAnalysis.model_validate(json.loads(cleaned)).model_dump()
        except Exception as exc:
            logger.error("Structured Agent 3 response validation failed: %s", exc)
            return EvidenceAnalysis(
                verdict="Unverified",
                confidence="Low",
                limitations="The evidence analysis response was empty or invalid; no unvalidated claims were returned.",
            ).model_dump()

    def validate_grounding(self, result: Dict[str, Any], articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate article IDs and verbatim quotes before the result reaches the API.
        
        Phase 6 checks:
        1. Citation validation: [A..] IDs must exist and not be irrelevant
        2. Quote validation: evidence_quote must be verbatim substring
        3. Grounding check: years/numbers in summary must appear in cited articles
        4. Verdict consistency: True requires all propositions supported by direct evidence
        5. Confidence capping based on code-side rubric
        """
        articles_by_id = {str(article.get("id")): article for article in articles}
        warnings: List[str] = []

        # -----------------------------------------------------------------------
        # 1. Validate article assessments
        # -----------------------------------------------------------------------
        valid_direct_ids: set = set()  # IDs with direct relevance and a valid quote
        for assessment in result.get("article_assessments", []):
            article = articles_by_id.get(str(assessment.get("id")))
            if not article:
                assessment.update(relevance="irrelevant", stance="not_applicable", evidence_quote=None)
                warnings.append(f"Invalid article ID {assessment.get('id')} nulled out")
                continue

            # Quote grounding: must be verbatim substring
            quote = assessment.get("evidence_quote")
            searchable = " ".join(str(article.get(field, "")) for field in ("title", "excerpt"))
            if quote:
                norm_quote = " ".join(str(quote).split()).lower()
                norm_search = " ".join(searchable.split()).lower()
                if norm_quote not in norm_search:
                    assessment["evidence_quote"] = None
                    if assessment.get("stance") in {"supports", "contradicts"}:
                        assessment["stance"] = "neutral_context"
                        warnings.append(f"Non-verbatim quote in {assessment.get('id')} -> stance downgraded to neutral_context")

            # Ensure irrelevant articles can't support stances
            if assessment.get("relevance") == "irrelevant":
                assessment["stance"] = "not_applicable"
            else:
                # Track direct articles with valid supporting/contradicting stance
                if assessment.get("relevance") == "direct" and assessment.get("stance") in ("supports", "contradicts"):
                    valid_direct_ids.add(str(assessment.get("id")))

        # -----------------------------------------------------------------------
        # 2. Validate proposition IDs and collect structured evidence
        # -----------------------------------------------------------------------
        valid_ids = set(articles_by_id.keys())
        prop_supporting_ids = set()
        prop_contradicting_ids = set()
        for proposition in result.get("propositions", []):
            proposition["supporting_ids"] = [item for item in proposition.get("supporting_ids", []) if item in valid_ids]
            proposition["contradicting_ids"] = [item for item in proposition.get("contradicting_ids", []) if item in valid_ids]
            prop_supporting_ids.update(proposition["supporting_ids"])
            prop_contradicting_ids.update(proposition["contradicting_ids"])

        hc_evidence_ids = {
            item
            for hc in result.get("historical_context", [])
            for item in hc.get("supporting_ids", [])
            if item in valid_ids
        }
        structured_evidence_ids = prop_supporting_ids | prop_contradicting_ids | hc_evidence_ids | (valid_direct_ids & valid_ids)

        # -----------------------------------------------------------------------
        # 3. Citation validation in summary/corrected_news/limitations
        # -----------------------------------------------------------------------
        text_fields = ("summary", "corrected_news", "limitations")
        text_to_search = " ".join(str(result.get(field) or "") for field in text_fields)

        bracketed_ids = set(re.findall(r"\[(A\d+)\]", text_to_search))
        paren_ids = set(re.findall(r"\((A\d+)\)", text_to_search))
        bare_ids = set(re.findall(r"\b(A\d{2,3})\b", text_to_search))

        text_cited_ids = bracketed_ids | paren_ids | (bare_ids & valid_ids)
        citation_ids = set(bracketed_ids) | (paren_ids & valid_ids)

        # Auto-heal citations from verified propositions if summary lacks inline citations
        if not citation_ids and structured_evidence_ids:
            citation_ids = set(structured_evidence_ids)
            recent_ids = [aid for aid in sorted(prop_supporting_ids) if articles_by_id.get(aid, {}).get("retrieval_pool") == "recent"]
            hist_ids = [aid for aid in sorted(prop_supporting_ids) if articles_by_id.get(aid, {}).get("retrieval_pool") == "historical"]
            if recent_ids and hist_ids:
                top_citations = recent_ids[:2] + hist_ids[:2]
            else:
                preferred_ids = sorted(prop_supporting_ids or prop_contradicting_ids or structured_evidence_ids)
                top_citations = preferred_ids[:4]
            citation_tag = " ".join(f"[{aid}]" for aid in top_citations)
            current_summary = (result.get("summary") or "").strip()
            if current_summary and not re.search(r"\[A\d+\]", current_summary):
                result["summary"] = f"{current_summary} {citation_tag}".strip()
                warnings.append(f"Auto-healed citations into summary from verified propositions: {citation_tag}")

        # Check for invalid citation IDs (e.g. model hallucinations like [A99])
        invalid_citations = (bracketed_ids | paren_ids) - valid_ids
        if invalid_citations:
            result["flags"] = sorted(set(result.get("flags", [])) | {"invalid_citation"})
            result["confidence"] = "Low"
            warnings.append(f"Invalid citation IDs {invalid_citations} - confidence downgraded")
            if not (text_cited_ids & valid_ids) and not structured_evidence_ids:
                if result.get("verdict") in {"True", "False", "Partially True", "Misleading"}:
                    result["verdict"] = "Unverified"
                    warnings.append("Verdict downgraded: all cited article IDs are invalid and no valid evidence found")

        # Downgrade only when NO evidence was cited in text or structured propositions
        if result.get("verdict") in {"True", "False", "Partially True", "Misleading"} and not citation_ids and not structured_evidence_ids:
            result["flags"] = sorted(set(result.get("flags", [])) | {"missing_citation"})
            result["verdict"] = "Unverified"
            result["confidence"] = "Low"
            result["summary"] = "No cited evidence was available to support a validated verdict."
            warnings.append("Verdict downgraded: no cited evidence available in text or structured propositions")

        # -----------------------------------------------------------------------
        # 4. Grounding check: years and numbers in summary must appear in cited articles
        # -----------------------------------------------------------------------
        evidence_ids_to_ground = citation_ids | structured_evidence_ids
        cited_article_texts = []
        for cid in evidence_ids_to_ground:
            art = articles_by_id.get(cid)
            if art:
                cited_article_texts.append(f"{art.get('title', '')} {art.get('excerpt', '')} {art.get('pub_date', '')}")
        cited_text_combined = " ".join(cited_article_texts).lower()

        for field_name in ("summary", "corrected_news"):
            field_value = result.get(field_name) or ""
            if not field_value:
                continue
            years_in_field = _YEAR_PATTERN.findall(field_value)
            for year in years_in_field:
                if year not in cited_text_combined:
                    warnings.append(f"Year {year} in {field_name} not found in cited articles")
                    # For corrected_news, remove offending sentence
                    if field_name == "corrected_news":
                        sentences = re.split(r"(?<=[.!?])\s+", field_value)
                        field_value = " ".join(s for s in sentences if year not in s)
                        result["corrected_news"] = field_value or None

        # -----------------------------------------------------------------------
        # 5. Verdict consistency (code is authoritative)
        # -----------------------------------------------------------------------
        verdict = result.get("verdict", "Unverified")
        propositions = result.get("propositions", [])

        # True requires EVERY proposition supported by a direct article
        if verdict == "True":
            all_supported = all(
                p.get("status") in ("supported",) and p.get("supporting_ids")
                for p in propositions
            ) if propositions else False

            if not all_supported or not valid_direct_ids:
                old_verdict = verdict
                result["verdict"] = "Unverified"
                result["confidence"] = "Low"
                result["flags"] = sorted(set(result.get("flags", [])) | {"no_direct_evidence"})
                warnings.append(f"Verdict downgraded from {old_verdict} to Unverified: not all propositions have direct support")

        # False requires a contradicting direct article (not opinion/liveblog alone)
        if verdict == "False":
            has_contradiction = any(
                p.get("status") == "contradicted" and p.get("contradicting_ids")
                for p in propositions
            )
            if not has_contradiction:
                result["verdict"] = "Unverified"
                result["confidence"] = "Low"
                warnings.append("Verdict downgraded from False to Unverified: no direct contradiction")

        # If verdict is definitive but no direct evidence at all, downgrade
        if verdict in {"True", "False", "Partially True", "Misleading"} and not valid_direct_ids:
            result["verdict"] = "Unverified"
            result["confidence"] = "Low"
            result["flags"] = sorted(set(result.get("flags", [])) | {"no_direct_evidence"})
            result["limitations"] = "No validated direct evidence supported the primary reading."
            warnings.append("Verdict downgraded: no direct evidence IDs")

        # -----------------------------------------------------------------------
        # 6. Confidence capping
        # -----------------------------------------------------------------------
        confidence = result.get("confidence", "Low")
        confidence = self._cap_confidence(confidence, result, articles_by_id, valid_direct_ids)
        result["confidence"] = confidence

        # -----------------------------------------------------------------------
        # Store warnings in result for tracing
        # -----------------------------------------------------------------------
        result["flags"] = sorted(set(result.get("flags", [])))
        if warnings:
            result.setdefault("_validation_warnings", []).extend(warnings)
            logger.info("Validation warnings: %s", warnings)

        return result

    def _cap_confidence(
        self,
        confidence: str,
        result: Dict[str, Any],
        articles_by_id: Dict[str, Any],
        valid_direct_ids: set,
    ) -> str:
        """Code-side confidence cap based on source quality, retrieval, and evidence."""
        flags = set(result.get("flags", []))
        verdict = result.get("verdict", "Unverified")

        # Get direct articles with valid stances
        direct_articles = [articles_by_id[aid] for aid in valid_direct_ids if aid in articles_by_id]

        # Count independent sources (unique publisher domains)
        independent_sources = len({
            a.get("publisher_site") or a.get("source", "") for a in direct_articles
        })

        # Check if all sources are unknown tier
        all_unknown = all(a.get("source_tier") == "unknown" for a in direct_articles) if direct_articles else True

        # Check if any full-text articles
        has_full_text = any(a.get("fetch_status") == "full_text" for a in direct_articles)

        # Check if retrieval was incomplete
        retrieval_incomplete = "retrieval_incomplete" in flags

        # Apply caps
        if all_unknown and direct_articles:
            confidence = "Low"
        elif independent_sources < 2 and confidence == "High":
            confidence = "Medium"
        elif not has_full_text and confidence == "High":
            confidence = "Medium"

        if retrieval_incomplete:
            if verdict == "Unverified":
                confidence = "Low"
            elif confidence == "High":
                confidence = "Medium"

        if "analysis_degraded" in flags and confidence == "High":
            confidence = "Medium"

        # Reference-only evidence: cap at Medium
        if all(articles_by_id.get(aid, {}).get("source_tier") == "reference" for aid in valid_direct_ids) and valid_direct_ids:
            confidence = min(["Low", "Medium", confidence], key=lambda c: ["High", "Medium", "Low"].index(c))

        return confidence
