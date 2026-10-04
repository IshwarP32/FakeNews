# Fake News Risk Analyzer - AI Context

> Persistent handoff file for future AI agents and project sessions. Update this file whenever a decision, implementation change, learning milestone, or blocker occurs.

## Project Snapshot

- **Project:** Fake News Risk Analyzer & Multi-Agent Fact Verifier
- **Current stage:** Reorganized Full-stack Application (`backend/` + `frontend/`) & Multi-Agent Verification System
- **Last updated:** 2026-10-04

- **Source document:** `docs/verification_methodology.md`, `docs/source_credibility.md`
- **Current workspace:** Contains the agentic verification service under `backend/` and the modular React frontend under `frontend/`.


## Problem

Misinformation spreads quickly and can create confusion, fear, and social disruption. A binary true/false result is often too limited for practical use because it does not communicate how suspicious, harmful, urgent, or sensitive a piece of content may be.

## Proposed Solution

Build an application that analyzes a news title, article, or claim and assigns an explainable misinformation verdict. The result considers:

- Multi-Agent research pipeline (Query Planner -> News Scraper -> Evidence Analyzer)
- Source reliability filtering across whitelisted Indian news agencies (PTI, UNI, PIB, TOI, NDTV, etc.)
- 10-model Gemini fallback list for robust API resilience
- Query execution history audit logs in `backend/history_logs/`
- AI-assisted evidence and explanation from trusted-source context

## High-Level Flow

1. **Input:** News title, article text, or claim
2. **Agent 1 (Query Planner):** Formulates targeted search queries for Indian news agencies
3. **Agent 2 (Live News Scraper):** Scrapes live RSS news feeds and filters against whitelisted outlets
4. **Agent 3 (Evidence Analyzer):** Cross-examines claim against gathered evidence using Gemini model fallback chain
5. **Output:** Verdict (True/False/Partially True/Unverified), Confidence level, Executive summary, Reasoning points, Verified sources, and Session history

## Technology Stack

- **Language/data:** Python 3.14+
- **Backend:** FastAPI service in `backend/` (`backend/main.py`)
- **API format:** REST JSON endpoints (`/api/analyze`) & SSE streaming (`/api/analyze/stream`)
- **Frontend:** React + Vite + Tailwind CSS in `frontend/` (`frontend/src/App.jsx`)
- **AI Engine:** Google GenAI SDK (`google-genai`) with fallback models

## Workspace Directory Hierarchy

```text
FakeNews/
├── backend/                   # FastAPI backend service
│   ├── agents/                # Planner, Scraper, Analyzer, Verifier
│   ├── config/                # Settings & model fallback list
│   ├── controllers/           # Endpoint request controllers
│   ├── routes/                # FastAPI routers (health, analyze)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # History logger
│   ├── utils/                 # Progress event emitters
│   ├── main.py                # FastAPI entry point
│   ├── requirements.txt
│   └── README.md
├── frontend/                  # React + Vite user interface
│   ├── src/
│   │   ├── assets/
│   │   ├── components/        # AnalysisForm, AnalysisResult, SourceList, etc.
│   │   ├── context/           # AnalysisContext state & reload persistence
│   │   ├── pages/             # Home page
│   │   ├── services/          # API fetch service
│   │   ├── App.jsx            # Root composition component
│   │   └── main.jsx
│   ├── package.json
│   └── README.md
├── docs/                      # Documentation
├── .gitignore
├── AI_CONTEXT.md
├── package.json
├── requirements.txt
└── startAll.bat                 # Windows testing launcher for backend + frontend
```

## Current Decisions

- **Multi-Agent Verification Architecture:** 3-Agent pipeline:
  - **Agent 1 (`planner.py`)**: Returns typed claim analysis and date-windowed queries through Gemini structured output.
  - **Agent 2 (`scraper.py`)**: Retrieves Google News RSS across recent/historical windows, scores concept coverage, and assigns stable article IDs and source tiers.
  - **Agent 3 (`analyzer.py` / `verifier.py`)**: Evaluates enriched article evidence with structured output; code validates IDs, quotes, relevance, confidence, and evidence/context grouping.
- **Versioned API contract:** `/api/analyze` and `/api/analyze/stream` return `schema_version: "2.0"`, separate `evidence_articles` and `context_articles`, and a `coverage` block.
- **Deterministic validation:** `eval/fixtures.jsonl` and `eval/run.py` cover old-only recurring evidence, near-miss events, and validated direct support.
- **Model Fallback Chain:** Automatically tries 10 fallback models (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.0-flash`, `gemini-3-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`) if a model is rate-limited (429), busy (503), or unavailable (404).
- **Session & History Persistence:**
  - Browser state is persisted across page reloads via `sessionStorage`.
  - Backend saves timestamped query execution audit logs in `backend/history_logs/`.
- **Repository Layout Reorganization:** Restructured repository layout into root `backend/`, `frontend/`, and a root-level Windows testing launcher (`startAll.bat`), following MediQueue / KingsMove modular standards.

---

## Progress Log

### 2026-09-21 - Repository Reorganization (MediQueue / KingsMove standard)

- Moved application code out of `web_app/` into root `backend/` and `frontend/`.
- Modularized backend:
  - `backend/config/`: App settings, paths, logger, fallback models list.
  - `backend/schemas/`: Pydantic request/response schemas.
  - `backend/utils/`: Progress event emitters.
  - `backend/services/`: History logger.
  - `backend/agents/`: Agent 1 (Planner), Agent 2 (Scraper), Agent 3 (Analyzer), and `GeminiVerifier`.
  - `backend/controllers/`: Request orchestration controllers.
  - `backend/routes/`: Health & Analyze FastAPI routers.
- Modularized frontend:
  - Split `App.jsx` into `AnalysisForm`, `AnalysisResult`, `SourceList`, `LoadingState`, `ErrorMessage`, `Home` page, and `AnalysisContext`.
  - Added `frontend/src/services/analysisApi.js` API client.
- Added the root testing launcher (`startAll.bat`) for starting the backend and frontend together.
- Updated `README.md`, `backend/README.md`, `frontend/README.md`, `.gitignore`, and `AI_CONTEXT.md`.

### 2026-09-28 - Intelligence Console UI and Deployment

- Redesigned the frontend as a dark slate/indigo intelligence console with dense input, pipeline, verdict, probability, evidence, and source surfaces.
- Added `VITE_API_URL` support for Vercel-to-Render API calls and configurable `CORS_ORIGINS` for production.
- Added `render.yaml` and `docs/deployment.md` covering Render and Vercel deployment.

### 2026-09-28 - VeriScan AI Interface Refinement

- Refined the frontend branding to `VeriScan AI` with the requested real-time verification hero, quick test samples, live three-agent execution timeline, and 12-column 7/5 analysis layout.
- Moved scraped evidence outlets into a full-width three-column grid with publisher, headline, URL, and external-link affordance.
