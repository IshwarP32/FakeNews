"""Agent 1: Search Query Planner.

Phase 2: Agent 1 picks window_role. Code (time_windows.py) computes all dates.
Improvements over baseline:
- Jaccard dedupe threshold raised to 0.85 (not 0.6) + exclude tokens common to ALL queries
- Outcome-neutral queries guaranteed (at least half); generate deterministic variants if needed
- must_have_terms validation: each group = aliases of ONE concept, no years/dates
- strict query validation: 2-6 tokens, strip date operators
- Backfill if fewer than N queries
- Never let claim_as_stated displace outcome_neutral
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.config import (
    MAX_QUERIES_PER_CLAIM,
    QUERY_PLANNER_PROMPT_LEN,
    logger,
)
from backend.config.prompts import QUERY_PLANNER_SYSTEM_INSTRUCTION, build_query_planner_prompt
from backend.schemas.verification import ClaimAnalysis, PlannedQuery, QueryPlan
from backend.time_windows import derive_all_windows
from backend.utils.progress import ProgressCallback, report

# Date operator pattern (should never appear in LLM query text)
_DATE_OPERATOR_RE = re.compile(r"\b(after|before|when|site):?\s*\d", re.IGNORECASE)
_DATE_TOKEN_RE = re.compile(r"\b(19|20)\d{2}\b")

# Priority order for deduplication preservation
_PURPOSE_PRIORITY = {
    "outcome_neutral": 0,
    "historical_origin": 1,
    "fact_check": 2,
    "claim_as_stated": 3,
    "disambiguation": 4,
    "official_source": 5,
}


class QueryPlannerAgent:
    """Agent 1 generates targeted search queries for Indian news sources."""

    def plan_queries(
        self,
        claim: str,
        llm_client,
        models: List[str],
        on_progress: Optional[ProgressCallback] = None,
        today: Optional[date] = None,
        max_rss_requests: int = 10,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        report(on_progress, "query_planning", "Agent 1 (Query Planner): Generating search queries...")
        logger.info("Agent 1: Planning search queries...")

        try:
            local_zone = ZoneInfo("Asia/Kolkata")
        except ZoneInfoNotFoundError:
            from datetime import timezone
            local_zone = timezone(timedelta(hours=5, minutes=30))
        if today is None:
            today = datetime.now(local_zone).date()

        prompt = build_query_planner_prompt(
            MAX_QUERIES_PER_CLAIM,
            claim[:QUERY_PLANNER_PROMPT_LEN],
            today.isoformat(),
        )
        raw_response_text = ""
        plan = QueryPlan(
            claim_analysis=ClaimAnalysis(normalized_claim=claim, primary_reading=claim),
            queries=[],
        )
        analysis_degraded = False

        try:
            resp, model_used = llm_client.generate(
                models=models,
                prompt=prompt,
                system_instruction=QUERY_PLANNER_SYSTEM_INSTRUCTION,
                response_schema=QueryPlan,
                thinking_level="low",
            )
            raw_response_text = getattr(resp, "text", "") or ""
            cleaned_text = raw_response_text.replace("```json", "").replace("```", "").strip()
            plan = QueryPlan.model_validate_json(cleaned_text)
        except Exception as e:
            logger.warning("Query planning failed or degraded: %s", e)
            analysis_degraded = True
            model_used = "none"

        ca = plan.claim_analysis
        if analysis_degraded:
            ca.analysis_degraded = True  # type: ignore[attr-defined]

        # Validate and repair must_have_terms
        ca.must_have_terms = self._validate_must_have_terms(ca)

        # Validate and select queries
        planned_queries, drop_log = self._select_queries(
            plan.queries, ca, today, n_target=MAX_QUERIES_PER_CLAIM
        )

        # Apply deterministic window derivation from time_windows.py
        queries_raw = [q.model_dump() for q in planned_queries]
        queries_with_windows = derive_all_windows(
            queries_from_llm=queries_raw,
            time_reference=ca.time_reference,
            explicit_dates=ca.explicit_dates,
            estimated_event_period=ca.estimated_event_period.model_dump() if ca.estimated_event_period else None,
            event_recurrence=ca.event_recurrence,
            today=today,
            max_rss_requests=max_rss_requests,
        )

        planner_log = {
            "prompt_sent": prompt,
            "raw_gemini_response": raw_response_text,
            "model_used": model_used,
            "claim_analysis": ca.model_dump(),
            "planned_queries": queries_with_windows,
            "drop_log": drop_log,
            "analysis_degraded": analysis_degraded,
        }

        return queries_with_windows, planner_log

    # -----------------------------------------------------------------------
    # Query validation and selection
    # -----------------------------------------------------------------------

    def _tokenise(self, q: str) -> frozenset[str]:
        return frozenset(re.findall(r"\w+", q.lower()))

    def _jaccard(self, a: frozenset, b: frozenset) -> float:
        u = a | b
        if not u:
            return 0.0
        return len(a & b) / len(u)

    def _jaccard_excluding_common(self, a: frozenset, b: frozenset, common: frozenset) -> float:
        a2, b2 = a - common, b - common
        u = a2 | b2
        if not u:
            return 0.0
        return len(a2 & b2) / len(u)

    def _strip_operators(self, q: str) -> str:
        """Remove date operators and site: operators the LLM may have written."""
        q = _DATE_OPERATOR_RE.sub("", q)
        # Remove site:domain patterns
        q = re.sub(r"\bsite:\S+", "", q, flags=re.IGNORECASE)
        # Remove after:/before: with dates
        q = re.sub(r"\b(after|before):\d{4}-\d{2}-\d{2}", "", q, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", q).strip()

    def _count_tokens(self, q: str) -> int:
        return len(re.findall(r"\w+", q))

    def _is_valid_query(self, q: str) -> bool:
        count = self._count_tokens(q)
        return 2 <= count <= 6

    def _select_queries(
        self,
        queries: List[PlannedQuery],
        ca: ClaimAnalysis,
        today: date,
        n_target: int,
    ) -> Tuple[List[PlannedQuery], List[Dict[str, Any]]]:
        """
        Select and validate queries:
        1. Strip operators, validate token count
        2. Sort by purpose priority (outcome_neutral first)
        3. Dedupe: exact (q, window_role, site_hint, language), then Jaccard > 0.85 excluding common tokens
        4. Guarantee at least ceil(n/2) outcome_neutral queries
        5. Drop non-news queries (official_source without site_hint)
        6. Backfill if fewer than n_target remain
        """
        drop_log: List[Dict[str, Any]] = []
        cleaned: List[PlannedQuery] = []

        for q_obj in queries:
            q_text = self._strip_operators(q_obj.q)
            if not self._is_valid_query(q_text):
                drop_log.append({"q": q_obj.q, "reason": f"invalid_token_count ({self._count_tokens(q_text)})"})
                continue
            if q_obj.purpose == "official_source" and not q_obj.site_hint:
                drop_log.append({"q": q_text, "reason": "official_source_without_site_hint"})
                continue
            q_copy = q_obj.model_copy()
            q_copy.q = q_text
            cleaned.append(q_copy)

        # Sort by priority (preserve within-priority order)
        cleaned.sort(key=lambda q: _PURPOSE_PRIORITY.get(q.purpose, 99))

        # Find tokens common to ALL queries (to exclude from Jaccard)
        all_token_sets = [self._tokenise(q.q) for q in cleaned]
        common_tokens: frozenset = frozenset()
        if all_token_sets:
            common_tokens = frozenset.intersection(*all_token_sets) if len(all_token_sets) > 1 else frozenset()

        # Deduplicate: exact first, then Jaccard > 0.85
        selected: List[PlannedQuery] = []
        seen_exact: set = set()
        seen_tokens: List[Tuple[frozenset, int]] = []  # (tokens, priority)

        for q_obj in cleaned:
            exact_key = (q_obj.q.lower().strip(), q_obj.window_role, q_obj.site_hint, q_obj.language)
            if exact_key in seen_exact:
                drop_log.append({"q": q_obj.q, "reason": "exact_duplicate"})
                continue

            tokens = self._tokenise(q_obj.q)
            priority = _PURPOSE_PRIORITY.get(q_obj.purpose, 99)
            is_dup = False

            for seen_tok, seen_priority in seen_tokens:
                j = self._jaccard_excluding_common(tokens, seen_tok, common_tokens)
                if j > 0.85:
                    # Keep whichever has higher priority (lower number)
                    if priority < seen_priority:
                        # New query has higher priority: replace? No - seen_tokens can't be easily removed.
                        # Since we sorted by priority, the first one we saw has equal or higher priority.
                        # So this new one is a dup of a higher-priority one.
                        pass
                    is_dup = True
                    drop_log.append({
                        "q": q_obj.q,
                        "reason": f"jaccard_duplicate (j={j:.2f})",
                        "jaccard_threshold": 0.85,
                    })
                    break

            if not is_dup:
                seen_exact.add(exact_key)
                seen_tokens.append((tokens, priority))
                selected.append(q_obj)

        # Count outcome_neutral and guarantee at least half
        n_neutral = sum(1 for q in selected if q.purpose == "outcome_neutral")
        n_required = max(1, (n_target + 1) // 2)  # ceil(n/2)
        missing_neutral = max(0, n_required - n_neutral)

        if missing_neutral > 0:
            logger.warning(
                "Only %d outcome_neutral queries; need %d. Generating deterministic variants.",
                n_neutral, n_required,
            )
            variants = self._generate_neutral_variants(ca, missing_neutral, today)
            for v in variants:
                drop_log.append({"q": v.q, "reason": "added_neutral_variant_backfill"})
            selected = variants + selected  # neutral variants go first

        # Limit to n_target
        if len(selected) > n_target:
            dropped = selected[n_target:]
            for dq in dropped:
                drop_log.append({"q": dq.q, "reason": "exceeds_n_target"})
            selected = selected[:n_target]

        # Backfill if still fewer than n_target
        if len(selected) < n_target:
            needed = n_target - len(selected)
            backfill = self._generate_neutral_variants(ca, needed, today, offset=len(selected))
            selected.extend(backfill[:needed])
            for bf in backfill[:needed]:
                drop_log.append({"q": bf.q, "reason": "backfill_to_n_target"})

        logger.info(
            "Query selection: %d input, %d selected, %d dropped. Neutral: %d",
            len(queries), len(selected), len(drop_log), sum(1 for q in selected if q.purpose == "outcome_neutral"),
        )
        return selected, drop_log

    def _generate_neutral_variants(
        self,
        ca: ClaimAnalysis,
        count: int,
        today: date,
        offset: int = 0,
    ) -> List[PlannedQuery]:
        """Generate deterministic outcome-neutral queries from entities and aliases."""
        variants: List[PlannedQuery] = []
        tr = ca.time_reference

        # Build entity keyword pairs
        entity_terms: List[str] = []
        for entity in ca.entities:
            entity_terms.append(entity.name)
            entity_terms.extend(entity.aliases[:2])

        # Use entity terms + event words (strip the outcome/verdict words)
        base_words = entity_terms[:4]
        if not base_words and ca.normalized_claim:
            words = re.findall(r"\w+", ca.normalized_claim)
            stop = {"won", "win", "wins", "winner", "lost", "arrested", "fired", "appointed",
                    "said", "claims", "the", "a", "an", "is", "was", "has", "have", "in",
                    "on", "at", "to", "of", "for", "by", "with", "and", "or"}
            base_words = [w for w in words if len(w) > 3 and w.lower() not in stop][:4]

        window_roles = ["latest", "historical", "claim_period", "recent_context"]

        for i in range(count):
            role = window_roles[min(i, len(window_roles) - 1)]
            if tr in ("explicit_date", "timeless_historical"):
                role = "claim_period"
            elif tr == "relative_current":
                role = "latest"

            q_text = " ".join(base_words[:(min(4, len(base_words) - offset + i + 1))])
            if not q_text or self._count_tokens(q_text) < 2:
                q_text = (ca.normalized_claim or "India news")[:50]
                # Keep only first few words
                q_text = " ".join(re.findall(r"\w+", q_text)[:4])

            variants.append(PlannedQuery(
                q=q_text,
                purpose="outcome_neutral",
                window_role=role,
                language="en",
            ))

        return variants

    # -----------------------------------------------------------------------
    # must_have_terms validation
    # -----------------------------------------------------------------------

    def _validate_must_have_terms(self, ca: ClaimAnalysis) -> List[List[str]]:
        """
        Validate and repair must_have_terms:
        - Each group should be aliases of ONE concept (alternatives, not AND)
        - Groups are AND-ed together
        - No year/date tokens inside a group
        - No group that mixes event name + entity name (different concepts)
        - 2-4 groups max
        """
        if not ca.must_have_terms:
            return self._derive_must_have_from_entities(ca)

        repaired: List[List[str]] = []
        for group in ca.must_have_terms:
            # Strip year/date tokens from group items
            cleaned_group = []
            for term in group:
                # Remove year-only terms
                if _DATE_TOKEN_RE.fullmatch(term.strip()):
                    continue
                # Remove terms that look like bare years/dates
                if re.match(r"^[\d\-/]+$", term.strip()):
                    continue
                cleaned_group.append(term)

            if not cleaned_group:
                continue

            # Heuristic: if group has > 3 items that are clearly different concepts, split
            # (We can't perfectly detect this without semantic understanding,
            # so we use a simple heuristic: if group contains both a long phrase
            # and short abbreviations, they're likely aliases of one concept = OK)
            # If group size is 1, it's fine.
            # The main bug from trace D3 was ONE group with three unrelated concepts.
            # We detect this by checking if the group has items that share no common tokens.
            if len(cleaned_group) >= 3:
                # Check if any two items share NO common tokens (clearly different concepts)
                tokens_per_item = [frozenset(re.findall(r"\w+", t.lower())) for t in cleaned_group]
                has_disjoint_pair = any(
                    not (tokens_per_item[i] & tokens_per_item[j])
                    for i in range(len(tokens_per_item))
                    for j in range(i + 1, len(tokens_per_item))
                    if len(tokens_per_item[i]) > 1 and len(tokens_per_item[j]) > 1
                )
                if has_disjoint_pair:
                    # Group mixes unrelated concepts. Keep only first item as a group.
                    logger.warning(
                        "must_have_terms group %r mixes unrelated concepts; keeping only first term",
                        cleaned_group,
                    )
                    repaired.append([cleaned_group[0]])
                    continue

            repaired.append(cleaned_group)

        # Cap to 4 groups
        repaired = repaired[:4]

        # If we ended up with no groups, derive from entities
        if not repaired:
            return self._derive_must_have_from_entities(ca)

        return repaired

    def _derive_must_have_from_entities(self, ca: ClaimAnalysis) -> List[List[str]]:
        """Derive must_have_terms from entities when the LLM output is invalid."""
        groups: List[List[str]] = []
        for entity in ca.entities[:4]:
            group = [entity.name] + entity.aliases[:3]
            groups.append(group)
        if not groups and ca.normalized_claim:
            # Extract key noun phrases as a single fallback group
            words = [w for w in re.findall(r"\b[A-Z][a-zA-Z]+\b", ca.normalized_claim) if len(w) > 2]
            if words:
                groups.append(words[:4])
        return groups[:4]
