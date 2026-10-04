# Verification Pipeline Audit & Resolution Status

Date: 2026-10-04

## Initial Architecture (Baseline Audit)

- Agent 1 in `backend/agents/planner.py` sent a free-form prompt to Gemini and expected a JSON array of query strings.
- Agent 2 in `backend/agents/scraper.py` queried Google News RSS, applied a site filter, fell back to an unrestricted query, and returned RSS metadata.
- Agent 3 in `backend/agents/verifier.py` received the claim plus numbered article title/source/publication-date lines and returned a free-form JSON verdict.
- `backend/agents/analyzer.py` parsed JSON with a regex fallback without strict schema validation or grounding validation.
- `backend/controllers/analyze_controller.py` exposed the verifier result directly to REST and SSE clients.
- `frontend/src/components/SourceList.jsx` rendered `grounding_sources` without stance grouping.

---

## Hypothesis Findings & Resolution Summary

1. **Newest-first sorting/truncation: CONFIRMED & RESOLVED.**
   - *Audit:* `scraper.py` sorted candidates strictly by publication date descending before returning them.
   - *Resolution:* Implemented two independent retrieval pools (`recent` and `historical`) with quota reservations (at least 1/3 of candidates per non-empty pool) and multi-factor scoring (must-have terms coverage, lexical similarity, source-tier priors).

2. **No date-window retrieval: CONFIRMED & RESOLVED.**
   - *Audit:* Requests lacked `after:` and `before:` date operators.
   - *Resolution:* `backend/time_windows.py` deterministically parses explicit years, month-years, full dates, and relative scopes to generate bounded RSS search queries.

3. **Weak near-miss filtering: CONFIRMED & RESOLVED.**
   - *Audit:* Substring matching allowed look-alikes (e.g. Inter IIT Tech Meet for a Sports Meet claim) to pass.
   - *Resolution:* Agent 1 generates structured `must_have_terms` concept groups. Candidates missing required concepts are filtered out, and near-miss entities are surfaced in Agent 3 assessments.

4. **Article text is absent: CONFIRMED & RESOLVED.**
   - *Audit:* Agent 3 received only article title, source, and date.
   - *Resolution:* Integrated `trafilatura` for full article text extraction with SSRF security boundaries and graceful snippet fallback.

5. **LLM indices trusted with unsafe fallback: CONFIRMED & RESOLVED.**
   - *Audit:* `verifier.py` mapped LLM numeric indices without semantic validation.
   - *Resolution:* Eliminated positional indices. Stable string IDs (`A01..A15`) are assigned in code; code maintains the canonical ID-to-article map and derives all evidence/context lists.

6. **Frontend renders one undifferentiated list: CONFIRMED & RESOLVED.**
   - *Audit:* All sources were rendered in a single flat list.
   - *Resolution:* Frontend (`frontend/src/components/SourceList.jsx` and `AnalysisResult.jsx`) categorizes sources into Supporting, Contradicting, and Context sections with tier badges, publication dates, and verbatim quotes.

7. **Verdict-first schema commitment: CONFIRMED & RESOLVED.**
   - *Audit:* Prompt demanded verdict first, inducing premature commitment.
   - *Resolution:* Reordered output schema so `article_assessments` and `propositions` precede `verdict`.

8. **Concatenated prompt instead of system/data separation: CONFIRMED & RESOLVED.**
   - *Audit:* Raw strings were concatenated with user input.
   - *Resolution:* System instructions are segregated from data payloads. Untrusted inputs (claim and article texts) are JSON-serialized inside `<claim_analysis>` and `<articles>` tags.

9. **Date handling is incomplete: CONFIRMED & RESOLVED.**
   - *Audit:* Dates used server-local time without timezone specification.
   - *Resolution:* Fixed today's date derivation to explicit `Asia/Kolkata` timezone in Python code.

10. **Validation/error handling incomplete: CONFIRMED & RESOLVED.**
    - *Audit:* Unhandled finish reasons, 429 quota cascades, and ungrounded citations.
    - *Resolution:* Central `LLMClient` with 4-way error classification, per-model cooldowns, strict Pydantic validation, verbatim quote checks, and safe degradation.

---

## Baseline Test Execution
- Deterministic test harness (`eval/run.py`): 33/33 tests passing.
- Backend compilation: 100% clean across all modules.
- Frontend build: Vite production build succeeded with 0 errors.
