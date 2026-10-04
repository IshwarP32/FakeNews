# Known Issues and Residual Risks

Date: 2026-10-04

## 1. Google News RSS Dynamic Redirects
- **Issue:** Google News RSS returns redirect links (`news.google.com/rss/articles/...`) rather than direct canonical publisher links.
- **Cause:** Google encodes landing URLs with rotating base64/batchexecute structures that cannot be decoded offline without HTTP resolution requests.
- **Handling/Workaround:** The pipeline inspects `<source url="...">` for publisher domain tiering and retains the redirect link for display. When full-text scraping fails due to redirect hops or paywalls, it safely falls back to `fetch_status: snippet_only` without dropping the candidate.

## 2. Paywalls and Anti-Scraping Defenses
- **Issue:** Premium news outlets (e.g. *The Hindu*, *The Indian Express*, *Economic Times*) may return 403/429 or paywall pay-gates when fetching article bodies.
- **Cause:** Cloudflare / Imperva bot mitigation on publisher domains.
- **Handling/Workaround:** SSRF-protected requests have strict timeouts (8s) and size limits. If full-text scraping via `trafilatura` fails, the pipeline uses the RSS headline and description snippet. The confidence rubric caps confidence to `Medium` if only snippet-level text is available.

## 3. Rate Limits and Quotas on Gemini Developer API
- **Issue:** Free-tier Gemini API keys face per-minute and per-day rate limits (429 RESOURCE_EXHAUSTED).
- **Cause:** Upstream API quota constraints.
- **Handling/Workaround:** `backend/llm_client.py` implements a 60-second cooldown per model and automatically falls back to secondary models (`gemini-2.5-flash`, `gemini-2.5-pro`). If all models are on cooldown, it terminates cleanly with `llm_quota_exhausted` and returns an explicit error state rather than hallucinating a default verdict.

## 4. Sparse Coverage for Pre-2015 Niche Regional Events
- **Issue:** Google News RSS index depth can be sparse for niche historical regional Indian news prior to 2015.
- **Cause:** Legacy publication digitisation and RSS indexing policies.
- **Handling/Workaround:** Phase 3 includes a multi-rung query widening ladder (widen window +/- 1 year, drop date operators, query top-tier domains directly) and conditional Wikipedia reference tier integration for historical windows. If coverage remains empty, Agent 3 is short-circuited and an honest `Unverified` verdict is produced with detailed coverage limitations.
