# Verification Methodology

The application performs fresh multi-agent analysis for every news claim request, following strict verification rules and model fallback resilience.

## Process

1. **Input Normalization:** Whitespace in the user claim or headline is cleaned and normalized.
2. **Agent 1 (Query Planning):** The Query Planner Agent generates targeted search queries for Indian news agencies.
3. **Agent 2 (Live News Scraping):** The News Scraper Agent searches live RSS news feeds for the planned queries, filtering results against a whitelist of verified Indian outlets (PTI, UNI, PIB, TOI, NDTV, The Hindu, Indian Express, HT, etc.).
4. **Agent 3 (Evidence Analysis):** The Evidence Analyzer Agent cross-examines the claim against gathered article evidence using Gemini with a 10-model fallback chain (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash`, etc.).
5. **Fail-Safe Search Grounding:** If 0 articles are scraped from live RSS, Agent 3 enables Gemini Search Grounding as a backup research layer.
6. **Query Audit Logging:** The system saves a timestamped JSON execution audit log in `backend/history_logs/`.

## Verdict Rules

- **True:** Whitelisted news sources directly support the main claim without contradiction.
- **False:** The evidence directly refutes the claim or reports a materially different event.
- **Partially True:** The central event is supported, but key details are wrong or exaggerated.
- **Unverified:** Evidence is insufficient or does not directly address the claim.
- High confidence requires direct matching evidence; otherwise confidence is Medium or Low.

Gemini requests use temperature `0` for consistency.