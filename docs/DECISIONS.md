# Architectural Decisions Log

This document records conservative design decisions, alternatives considered, and rationales across pipeline implementation phases as required by Section 0 of the project brief.

---

## Decision 1: Dedicated LLM Client with Strict 4-Way Error Classification
- **Decision:** Implement a centralized `LLMClient` (`backend/llm_client.py`) with explicit classification into `CONFIG_ERROR`, `QUOTA_EXHAUSTED`, `TRANSIENT`, and `CONTENT`.
- **Alternatives Considered:**
  1. Catch-all retry loop across all exceptions.
  2. Relying on Google GenAI SDK's internal retry mechanism alone.
- **Rationale:** Catch-all retries waste quota and cause cascading failover loops on deterministic invalid argument or schema validation errors. 400/401/403 errors are configuration/client bugs that must fail fast with 1 attempt. 429 errors require individual model cooldown (60s default) and next-model fallback. 500/503 errors warrant exponential backoff with jitter.

---

## Decision 2: Reference Tier (Wikipedia API) Integration
- **Decision:** Implement reference tier support behind a configuration setting (`ENABLE_REFERENCE_TIER = True` for historical queries when news RSS returns < 3 items), explicitly tagged as `source_tier: reference` with `badge: "Reference (not news)"`.
- **Alternatives Considered:**
  1. Relying strictly on Google News RSS regardless of result count.
  2. Unconditionally querying Wikipedia for all claims.
- **Rationale:** Google News RSS historical coverage for niche pre-2015 events can be sparse or yield non-canonical aggregator pages. Wikipedia extracts provide authoritative factual baselines for settled historical events (e.g. 1950 Constitution, 2016 awards) while never being allowed to justify `High` confidence alone.

---

## Decision 3: Code-Side Authority for Grounding and Verdict Consistency
- **Decision:** Code strictly validates all LLM outputs before returning them to the frontend or caller. Agent 3 LLM produces an initial assessment, but deterministic Python code:
  - Validates all citations `[A..]` exist in the supplied article map.
  - Verifies that `evidence_quote` is a verbatim substring of the article title or excerpt; non-verbatim quotes cause an automatic stance downgrade to `neutral_context`.
  - Enforces verdict caps: `True` is rejected if any proposition lacks direct supporting evidence or has contradictory evidence.
  - Implements the recycled-news rule: undated claims with only historical evidence cannot receive `True`.
  - Caps confidence to `min(model_confidence, code_rubric_cap)`.
- **Alternatives Considered:**
  1. Trusting the LLM's parsed verdict and confidence directly.
  2. Asking the LLM to self-critique in a secondary verification pass.
- **Rationale:** LLMs suffer from recency bias, sycophancy, and hallucinated citations. Deterministic code guarantees that 0 ungrounded citations or impossible verdict states can ever reach users or API consumers.

---

## Decision 4: Structural Security via JSON-in-XML Tag Containment
- **Decision:** Pass all untrusted user inputs (claim, article excerpts, titles) as JSON-serialized payloads inside semantic XML tags (`<claim_analysis>{...}</claim_analysis>`, `<articles>[{...}]</articles>`).
- **Alternatives Considered:**
  1. Python `repr()` / `str(dict)` string interpolation.
  2. Markdown lists with raw user strings.
- **Rationale:** Python `repr()` uses single quotes, which are invalid JSON and prone to parsing failures (Trace D6). Raw XML tag concatenation allows malicious inputs like `</articles>` to break the prompt enclosure. JSON serialization safely escapes strings while maintaining clean machine readability for the model.

---

## Decision 5: Two-Pool Candidate Retrieval with Reserved Quotas
- **Decision:** Partition retrieval candidates into two independent pools (`recent` and `historical`), allocating at least 1/3 of the total candidate budget (`MAX_CANDIDATES = 15`) to each non-empty pool.
- **Alternatives Considered:**
  1. Global sorting by publication date or lexical relevance score.
  2. Only retrieving historical articles when the claim explicitly mentions a past year.
- **Rationale:** Claims often circulate as recycled news (e.g. undated sports tournament wins or viral hoaxes). If candidates are sorted by publication date descending, recent unrelated or near-miss articles crowd out the older genuine event. The two-pool architecture ensures historical evidence reaches Agent 3.

---

## Decision 6: Zero-Article Short-Circuit
- **Decision:** If Agent 2 retrieves 0 usable articles, Agent 3 is completely bypassed. A deterministic `Unverified` result is returned with clear limitations built directly from search coverage metadata.
- **Alternatives Considered:**
  1. Calling Agent 3 with an empty articles list to let the LLM generate a summary.
- **Rationale:** Asking an LLM to evaluate a claim with 0 evidence leads to hallucinated background knowledge leaks, violating Rule 1 ("Agent 3 judges ONLY supplied articles"). Bypassing Gemini saves API latency and quota while guaranteeing factual honesty.
