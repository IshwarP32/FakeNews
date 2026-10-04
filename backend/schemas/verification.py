"""Typed contracts for the multi-agent verification pipeline.

Schema version: 2.0 (additive changes only)
If any field is renamed/removed/changes meaning, bump to 2.1 and update frontend.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Agent 1 output schemas
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)


class EstimatedEventPeriod(BaseModel):
    """LLM's estimate of when the claimed event occurred."""
    start_year: int = 0
    end_year: int = 0
    basis: Literal["stated_in_claim", "model_guess", "unknown"] = "unknown"


class ClaimAnalysis(BaseModel):
    normalized_claim: str = ""
    language: Literal["en", "hi", "hinglish", "other"] = "en"
    check_worthiness: Literal["checkable", "opinion", "prediction", "satire_or_unclear"] = "checkable"
    propositions: list[str] = Field(default_factory=list, max_length=4)
    time_reference: Literal[
        "explicit_date", "relative_current", "implicit_news_like", "timeless_historical"
    ] = "implicit_news_like"
    event_recurrence: Literal["one_off", "recurring", "ongoing_state", "unknown"] = "unknown"
    explicit_dates: list[str] = Field(default_factory=list)
    estimated_event_period: EstimatedEventPeriod = Field(default_factory=EstimatedEventPeriod)
    primary_reading: str = ""
    alternate_readings: list[str] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    must_have_terms: list[list[str]] = Field(default_factory=list)
    likely_confusions: list[str] = Field(default_factory=list)


class PlannedQuery(BaseModel):
    """Agent 1 query plan - NO after/before (code derives dates from window_role)."""
    q: str = Field(min_length=1)
    purpose: Literal[
        "outcome_neutral",
        "claim_as_stated",
        "historical_origin",
        "official_source",
        "fact_check",
        "disambiguation",
    ] = "outcome_neutral"
    window_role: Literal[
        "claim_period",
        "latest",
        "historical",
        "recent_context",
    ] = "latest"
    language: Literal["en", "hi"] = "en"
    site_hint: Optional[str] = None


class QueryPlan(BaseModel):
    claim_analysis: ClaimAnalysis
    queries: list[PlannedQuery] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent 3 output schemas
# ---------------------------------------------------------------------------

class EventDate(BaseModel):
    value: Optional[str] = None
    basis: Literal["stated_in_text", "inferred_from_pub_date", "unknown"] = "unknown"


class ArticleAssessment(BaseModel):
    id: str
    relevance: Literal["direct", "contextual", "irrelevant"] = "irrelevant"
    relevance_reason: str = ""
    near_miss_entity: Optional[str] = None
    stance: Literal["supports", "contradicts", "neutral_context", "not_applicable"] = "not_applicable"
    evidence_quote: Optional[str] = None
    event_date: EventDate = Field(default_factory=lambda: EventDate())
    applies_to_reading: Literal["primary", "alternate", "neither"] = "neither"
    article_kind: Literal[
        "straight_report",
        "official_statement",
        "fact_check",
        "opinion_or_analysis",
        "retrospective_or_explainer",
        "liveblog_or_roundup",
        "unclear",
    ] = "unclear"


class PropositionAssessment(BaseModel):
    text: str
    status: Literal[
        "supported",
        "contradicted",
        "partially_supported",
        "no_direct_evidence",
        "contested",
    ] = "no_direct_evidence"
    supporting_ids: list[str] = Field(default_factory=list)
    contradicting_ids: list[str] = Field(default_factory=list)
    note: str = ""


class TemporalAnalysis(BaseModel):
    time_reference: str = "implicit_news_like"
    primary_reading_applied: str = ""
    evidence_found_for_primary_reading: bool = False
    recycled_news_suspected: bool = False
    notes: str = ""


class HistoricalContext(BaseModel):
    event_date: str = ""
    statement: str = ""
    supporting_ids: list[str] = Field(default_factory=list)


class CoverageWindow(BaseModel):
    after: Optional[str] = None
    before: Optional[str] = None
    purpose: str = ""
    role: str = ""
    status: Literal["ok", "empty", "failed"] = "ok"
    items_returned: int = 0
    items_kept: int = 0
    error: Optional[str] = None
    rss_url: Optional[str] = None
    ladder_rung: Optional[str] = None


class CoverageDateRange(BaseModel):
    earliest_publication: Optional[str] = None
    latest_publication: Optional[str] = None


class EvidenceAnalysis(BaseModel):
    # Assessments first, verdict last (field order matters for Gemini structured output)
    article_assessments: list[ArticleAssessment] = Field(default_factory=list)
    propositions: list[PropositionAssessment] = Field(default_factory=list)
    temporal_analysis: TemporalAnalysis = Field(default_factory=TemporalAnalysis)
    historical_context: list[HistoricalContext] = Field(default_factory=list)
    verdict: Literal[
        "True",
        "False",
        "Partially True",
        "Misleading",
        "Unverified",
        "Not Checkable",
    ] = "Unverified"
    flags: list[str] = Field(default_factory=list)
    confidence: Literal["High", "Medium", "Low"] = "Low"
    summary: str = ""
    corrected_news: Optional[str] = None
    limitations: str = ""


class Coverage(BaseModel):
    queries_run: int = 0
    windows: list[CoverageWindow] = Field(default_factory=list)
    articles_retrieved: int = 0
    articles_ranked: int = 0
    articles_analysed: int = 0
    independent_sources: int = 0
    date_range: CoverageDateRange = Field(default_factory=CoverageDateRange)
    empty_pools: list[str] = Field(default_factory=list)
    retrieval_incomplete: bool = False


class VerificationResult(BaseModel):
    schema_version: str = "2.0"
    claim: str
    verdict: EvidenceAnalysis
    evidence_articles: list[dict[str, object]] = Field(default_factory=list)
    context_articles: list[dict[str, object]] = Field(default_factory=list)
    coverage: Coverage = Field(default_factory=Coverage)
