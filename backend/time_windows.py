"""Time window derivation module for the fake-news verification pipeline.

Phase 2 requirement: ALL date logic lives here. Agent 1 never writes dates.
The LLM picks a window_role; this module computes the actual after/before dates.

Rules:
- explicit_date claims: window must contain the stated year/month/date
- All windows: after < before always
- Never fall back to a recent-90-days window for explicit_date claims
- Agent 1 may only WIDEN a derived window, never narrow it
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("fake_news_verifier")


@dataclass
class DateWindow:
    after: date
    before: date
    role: str         # claim_period | latest | historical | recent_context
    source: str       # how we derived it
    time_reference: str = ""

    def __post_init__(self):
        if self.after >= self.before:
            # Ensure after < before always
            self.before = self.after + timedelta(days=1)

    def to_dict(self) -> Dict[str, str]:
        return {
            "after": self.after.isoformat(),
            "before": self.before.isoformat(),
            "role": self.role,
            "source": self.source,
        }

    def contains_year(self, year: int) -> bool:
        return self.after.year <= year <= self.before.year

    def widen(self, new_after: date, new_before: date) -> "DateWindow":
        """Return a new window widened to include the given range."""
        return DateWindow(
            after=min(self.after, new_after),
            before=max(self.before, new_before),
            role=self.role,
            source=f"{self.source}+widened",
            time_reference=self.time_reference,
        )


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_YEAR_PATTERN = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")
_MONTH_YEAR_PATTERN = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"[,\s]+(\d{4})\b",
    re.IGNORECASE,
)
_FULL_DATE_DMY = re.compile(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b")
_FULL_DATE_MDY = re.compile(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b")
_RANGE_HYPHEN = re.compile(r"\b(19\d{2}|20[0-2]\d)\s*[-\u2013\u2014]\s*(19\d{2}|20[0-2]\d)\b")
_RANGE_BETWEEN = re.compile(
    r"\bbetween\s+(19\d{2}|20[0-2]\d)\s+and\s+(19\d{2}|20[0-2]\d)\b",
    re.IGNORECASE,
)

_MONTH_NAME_TO_NUM = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _last_day_of_month(year: int, month: int) -> int:
    """Return last day of given month/year."""
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - timedelta(days=1)).day


def parse_explicit_dates(date_strings: List[str], today: date) -> Optional[Tuple[date, date]]:
    """
    Parse a list of explicit date strings (as returned by Agent 1) into a (start, end) range.

    Returns the WIDEST range that contains all parsed dates, or None if nothing parseable.
    Never returns a range that excludes the stated year(s).
    """
    earliest: Optional[date] = None
    latest: Optional[date] = None

    for ds in date_strings:
        text = ds.strip()

        # Try range "2019-2021" or "between 2018 and 2020"
        range_match = _RANGE_HYPHEN.search(text) or _RANGE_BETWEEN.search(text)
        if range_match:
            y1, y2 = sorted([int(range_match.group(1)), int(range_match.group(2))])
            s, e = date(y1, 1, 1) - timedelta(days=7), date(y2, 12, 31) + timedelta(days=90)
            earliest = s if earliest is None else min(earliest, s)
            latest = e if latest is None else max(latest, e)
            continue

        # Try month-year "January 2016"
        my = _MONTH_YEAR_PATTERN.search(text)
        if my:
            month_name = my.group(1).lower()[:3]
            month_num = _MONTH_NAME_TO_NUM.get(month_name, 1)
            year = int(my.group(2))
            s = date(year, month_num, 1) - timedelta(days=7)
            last = _last_day_of_month(year, month_num)
            e = date(year, month_num, last) + timedelta(days=60)
            earliest = s if earliest is None else min(earliest, s)
            latest = e if latest is None else max(latest, e)
            continue

        # Try full date "23 August 2023" or "2023-08-23"
        # ISO format
        iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
        if iso_match:
            try:
                d = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
                s, e = d - timedelta(days=7), d + timedelta(days=60)
                earliest = s if earliest is None else min(earliest, s)
                latest = e if latest is None else max(latest, e)
                continue
            except ValueError:
                pass

        # Written date "23 August 2023"
        written_match = re.search(
            r"\b(\d{1,2})\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"\s+(\d{4})\b",
            text, re.IGNORECASE,
        )
        if written_match:
            try:
                day = int(written_match.group(1))
                month_num = _MONTH_NAME_TO_NUM[written_match.group(2).lower()[:3]]
                year = int(written_match.group(3))
                d = date(year, month_num, day)
                s, e = d - timedelta(days=7), d + timedelta(days=60)
                earliest = s if earliest is None else min(earliest, s)
                latest = e if latest is None else max(latest, e)
                continue
            except (ValueError, KeyError):
                pass

        # Year only "2016"
        year_match = _YEAR_PATTERN.search(text)
        if year_match:
            year = int(year_match.group(1))
            s = date(year, 1, 1) - timedelta(days=7)
            e = date(year, 12, 31) + timedelta(days=90)
            earliest = s if earliest is None else min(earliest, s)
            latest = e if latest is None else max(latest, e)
            continue

    if earliest is not None and latest is not None:
        return earliest, latest
    return None


# ---------------------------------------------------------------------------
# Historical slices: going back from a reference date
# These are configurable; values in years
# ---------------------------------------------------------------------------
HISTORICAL_SLICES = [
    (-3, -14 / 12),   # 3 years back to ~14 months ago
    (-6, -3),          # 6 to 3 years
    (-10, -6),         # 10 to 6 years
]


def _years_offset(base: date, years_float: float) -> date:
    """Add fractional years to a date (approximate)."""
    days = int(years_float * 365.25)
    return base + timedelta(days=days)


def derive_window(
    window_role: str,
    time_reference: str,
    explicit_dates: List[str],
    estimated_event_period: Optional[Dict[str, Any]] = None,
    event_recurrence: str = "unknown",
    today: Optional[date] = None,
    slice_index: int = 0,  # for historical multi-slice
) -> DateWindow:
    """
    Derive a concrete DateWindow from Agent 1's window_role and claim metadata.

    This is the SINGLE source of truth for all date computation.
    Agent 1 never writes dates; Agent 1 only provides window_role.

    Args:
        window_role: one of claim_period | latest | historical | recent_context
        time_reference: explicit_date | relative_current | implicit_news_like | timeless_historical
        explicit_dates: list of date strings from claim_analysis
        estimated_event_period: {start_year, end_year, basis} from claim_analysis
        event_recurrence: one_off | recurring | ongoing_state | unknown
        today: override today (for testing)
        slice_index: which historical slice to use (0=most recent, 1=middle, 2=oldest)

    Returns:
        DateWindow with after < before guaranteed
    """
    if today is None:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    role = window_role or "latest"
    tr = time_reference or "implicit_news_like"

    # -----------------------------------------------------------------------
    # claim_period: use the explicit date range, or estimated period
    # -----------------------------------------------------------------------
    if role == "claim_period":
        if explicit_dates:
            parsed = parse_explicit_dates(explicit_dates, today)
            if parsed:
                after, before = parsed
                return DateWindow(after=after, before=before, role=role,
                                  source="explicit_dates_parsed", time_reference=tr)

        # Fall back to estimated_event_period (basis: stated_in_claim or model_guess)
        if estimated_event_period:
            start_year = estimated_event_period.get("start_year", 0)
            end_year = estimated_event_period.get("end_year", 0)
            basis = estimated_event_period.get("basis", "unknown")
            if start_year > 0 and end_year > 0 and basis != "unknown":
                padding = timedelta(days=365) if basis == "model_guess" else timedelta(days=7)
                after = date(start_year, 1, 1) - padding
                before = date(end_year, 12, 31) + timedelta(days=90)
                return DateWindow(after=after, before=before, role=role,
                                  source=f"estimated_period_{basis}", time_reference=tr)

        # For explicit_date without parseable explicit_dates, use historical slices
        # (never fall back to last-90-days for an explicit_date claim)
        logger.warning("explicit_date claim but no parseable explicit_dates; using 3-year historical window")
        after = today - timedelta(days=3 * 365)
        before = today
        return DateWindow(after=after, before=before, role=role,
                          source="explicit_date_fallback_no_dates", time_reference=tr)

    # -----------------------------------------------------------------------
    # latest: recent window
    # -----------------------------------------------------------------------
    if role == "latest" or role == "recent_context":
        # Annual or rare recurring events: wider window
        if event_recurrence in ("recurring",) and tr == "implicit_news_like":
            after = today - timedelta(days=int(14 * 30.44))  # ~14 months
        else:
            after = today - timedelta(days=90)
        before = today + timedelta(days=1)
        return DateWindow(after=after, before=before, role=role,
                          source="latest_relative", time_reference=tr)

    # -----------------------------------------------------------------------
    # historical: older occurrences
    # -----------------------------------------------------------------------
    if role == "historical":
        # If estimated_event_period is given by the claim, use it
        if estimated_event_period:
            start_year = estimated_event_period.get("start_year", 0)
            end_year = estimated_event_period.get("end_year", 0)
            basis = estimated_event_period.get("basis", "unknown")
            if start_year > 0 and basis != "unknown":
                padding = timedelta(days=365) if basis == "model_guess" else timedelta(days=7)
                after = date(start_year, 1, 1) - padding
                before_year = end_year if end_year > 0 else start_year
                before = date(before_year, 12, 31) + timedelta(days=90)
                return DateWindow(after=after, before=before, role=role,
                                  source=f"historical_estimated_{basis}", time_reference=tr)

        # Use pre-defined slices going back from today
        slices = HISTORICAL_SLICES
        idx = min(slice_index, len(slices) - 1)
        start_yrs, end_yrs = slices[idx]
        after = _years_offset(today, start_yrs)
        before = _years_offset(today, end_yrs)
        if before <= after:
            before = after + timedelta(days=1)
        return DateWindow(after=after, before=before, role=role,
                          source=f"historical_slice_{idx}", time_reference=tr)

    # Fallback: treat unknown roles as recent_context
    after = today - timedelta(days=90)
    before = today + timedelta(days=1)
    return DateWindow(after=after, before=before, role=role,
                      source=f"fallback_unknown_role_{role}", time_reference=tr)


def derive_all_windows(
    queries_from_llm: List[Dict[str, Any]],
    time_reference: str,
    explicit_dates: List[str],
    estimated_event_period: Optional[Dict[str, Any]],
    event_recurrence: str,
    today: Optional[date] = None,
    max_rss_requests: int = 10,
) -> List[Dict[str, Any]]:
    """
    Take Agent 1's query plan (with window_role, no dates) and produce
    queries with concrete after/before dates attached.

    Returns a list of query dicts with after/before set.
    Logs each derivation for tracing.
    Respects max_rss_requests budget (drops lowest-priority queries with logging).
    """
    if today is None:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date()

    enriched = []
    historical_slice_counter = 0

    for query in queries_from_llm:
        role = query.get("window_role", "latest")
        if role == "historical":
            slice_idx = historical_slice_counter
            historical_slice_counter += 1
        else:
            slice_idx = 0

        window = derive_window(
            window_role=role,
            time_reference=time_reference,
            explicit_dates=explicit_dates,
            estimated_event_period=estimated_event_period,
            event_recurrence=event_recurrence,
            today=today,
            slice_index=slice_idx,
        )

        q_copy = dict(query)
        q_copy["after"] = window.after.isoformat()
        q_copy["before"] = window.before.isoformat()
        q_copy["_window_source"] = window.source
        q_copy["_window_role"] = window.role

        logger.debug(
            "Window derived: query=%r role=%s after=%s before=%s source=%s",
            query.get("q", ""),
            window.role,
            window.after,
            window.before,
            window.source,
        )
        enriched.append(q_copy)

    # Budget enforcement
    if len(enriched) > max_rss_requests:
        logger.warning(
            "Query count %d exceeds MAX_RSS_REQUESTS %d; dropping lowest-priority queries",
            len(enriched), max_rss_requests,
        )
        # Priority order: outcome_neutral > historical_origin > fact_check > claim_as_stated > others
        priority = {
            "outcome_neutral": 0,
            "historical_origin": 1,
            "fact_check": 2,
            "claim_as_stated": 3,
            "disambiguation": 4,
            "official_source": 5,
        }
        enriched.sort(key=lambda q: priority.get(q.get("purpose", ""), 99))
        dropped = enriched[max_rss_requests:]
        for dq in dropped:
            logger.warning("Budget: dropping query %r (purpose=%s)", dq.get("q", ""), dq.get("purpose", ""))
        enriched = enriched[:max_rss_requests]

    return enriched
