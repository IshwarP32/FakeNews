# VeriScan AI: Fake News Risk Analyzer & Multi-Agent Fact Verifier

A robust, multi-agent AI verification system designed to verify both current and historical Indian news claims with high precision, grounded citations, and zero tolerance for hallucination or unvalidated assertions.

---

## Key Architecture & Guarantees

1. **Agent 1 (Query Planner):** Analyzes claim propositions, temporal scope, entities, and must-have terms. Plans outcome-neutral search queries with deterministic date windows.
2. **Agent 2 (News Scraper & Retriever):** Retrieves candidates across recent and historical date windows via Google News RSS, ranks candidates via pool quotas, enforces SSRF protections, and fetches verified article text.
3. **Agent 3 (Evidence Analyzer):** Evaluates supplied articles strictly as data inside JSON-escaped XML tags. No tools are permitted for Agent 3.
4. **Code-Side Authority:** Deterministic Python logic validates all citations, quote grounding, verdict consistency, confidence caps, and safe degradation. Absence of evidence never produces a "False" verdict.

---

## Repository Structure

```text
FakeNews/
├── backend/                   # FastAPI backend service & Multi-Agent Pipeline
│   ├── agents/                # Query Planner (Agent 1), News Scraper (Agent 2), Evidence Analyzer (Agent 3)
│   ├── config/                # Settings, model capability tables, source tiers, system prompts
│   ├── controllers/           # REST and SSE streaming controllers
│   ├── routes/                # FastAPI health and analysis routers
│   ├── schemas/               # Pydantic schemas (Agent 1, Agent 3, API response)
│   ├── services/              # History and telemetry logging
│   ├── llm_client.py          # Central Gemini client (error classification, cooldown, fallbacks)
│   ├── time_windows.py        # Deterministic date-window parser and derivation logic
│   ├── verify.py              # CLI verification entrypoint with trace support
│   └── main.py                # FastAPI application entrypoint
├── frontend/                  # React + Vite + Tailwind CSS interface
├── eval/                      # Evaluation suite and fixtures
│   ├── baseline_claims.jsonl  # 16-claim baseline dataset (current & historical)
│   ├── fixtures.jsonl         # Regression test fixtures
│   └── run.py                 # Deterministic and live evaluation harness
└── docs/                      # Technical specifications, audits, decisions, and notes
    ├── AUDIT.md
    ├── DECISIONS.md
    ├── KNOWN_ISSUES.md
    ├── google_news_rss_notes.md
    └── TASK.md
```

---

## Quickstart

### 1. Python Environment Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your Gemini API key in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Running the Full Stack App
- **Option A (One-click launcher):**
  Double-click `startAll.bat` in the repository root.
- **Option B (Manual):**
  - **Backend (FastAPI):**
    ```powershell
    python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
    ```
    API documentation is accessible at `http://localhost:8000/docs`.
  - **Frontend (Vite + React):**
    ```powershell
    cd frontend
    npm run dev
    ```
    UI is accessible at `http://localhost:5173`.

---

## Running the Verification CLI with Tracing

You can verify any news claim directly from the command line with optional telemetry tracing:

```powershell
# Basic verification:
python -m backend.verify --claim "Chandrayaan-3 landed on the Moon on 23 August 2023"

# Verification with execution trace (query derivation, retrieval windows, candidate ranking):
python -m backend.verify --claim "IIT Madras won Inter IIT sports meet in 2016" --trace

# Raw JSON output:
python -m backend.verify --claim "India won ICC T20 World Cup 2024" --json
```

---

## Running Evaluations

### Deterministic Test Suite (Offline, Mocks & Fixtures)
Runs all 33 unit and regression tests without making external network or Gemini API calls:
```powershell
python eval/run.py
```
This tests:
- Schema transformations (ensuring compatibility without `additionalProperties`)
- Deterministic date-window derivations across explicit dates, years, ranges, and relative current time
- Outcome-neutral query balance and Jaccard deduplication
- Error classifications (CONFIG, QUOTA 429, TRANSIENT 503, CONTENT)
- Zero-article short-circuits and safe degradation
- Verbatim quote grounding and stance validation
- Verdict consistency rules and confidence capping
- Prompt injection protection via JSON encapsulation

### Live Model Evals (Budgeted Gemini Calls)
To run evaluations against live Gemini models:
```powershell
python eval/run.py --live --max-live-calls 3
```

---

## Configuration & Customization

### Editing Source Credibility Tiers (`backend/config/sources.yaml`)
Publisher credibility tiers are configured in `backend/config/sources.yaml`:
```yaml
official:
  - pib.gov.in
  - isro.gov.in
  - sci.gov.in

wire_national:
  - ptinews.com
  - uniindia.com
  - aninews.in

factchecker:
  - altnews.in
  - boomlive.in
  - thequint.com
```
Add new domains to the appropriate tier to adjust publisher weighting in candidate ranking.

### Changing Models and Capability Table (`backend/config/settings.py`)
Model fallback priority chains and capability parameters are centrally managed in `backend/config/settings.py`:
- `PLANNER_MODELS`: List of models for Agent 1 (e.g. `["gemini-2.5-flash", "gemini-2.0-flash"]`).
- `ANALYZER_MODELS`: List of models for Agent 3 (e.g. `["gemini-2.5-pro", "gemini-2.5-flash"]`).
- `MODEL_CAPABILITIES`: Mapping specifying whether each model supports thinking budgets/levels and structured outputs:
  ```python
  MODEL_CAPABILITIES = {
      "gemini-2.5-flash": {
          "supports_thinking": True,
          "thinking_param": "level",
          "supports_structured_output": True,
      },
      ...
  }
  ```