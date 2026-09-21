# Fake News Risk Analyzer - AI Context

> Persistent handoff file for future AI agents and project sessions. Update this file whenever a decision, implementation change, learning milestone, or blocker occurs.

## Project Snapshot

- **Project:** Fake News Risk Analyzer & Multi-Agent Fact Verifier
- **Current stage:** Reorganized Full-stack Application (`backend/` + `frontend/`) & Multi-Agent Verification System
- **Last updated:** 2026-09-21

- **Source document:** `docs/verification_methodology.md`, `docs/source_credibility.md`
- **Current workspace:** Contains datasets under `data/`, ML model under `models/`, ML source under `src/fake_news_risk/`, training scripts under `scripts/`, reorganized FastAPI service under `backend/`, and modular React frontend under `frontend/`.


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
- **NLP/ML:** TF-IDF + Logistic Regression baseline in `src/fake_news_risk/` & `scripts/train_model.py`
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
│   ├── services/              # History logger & ML predictor
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
├── data/                      # Kaggle datasets (Fake.csv, True.csv)
├── docs/                      # Documentation
├── models/                    # Model artifacts (model.joblib)
├── reports/                   # Performance reports
├── scripts/                   # Training scripts (train_model.py)
├── src/                       # Reusable ML package (fake_news_risk)
├── .gitignore
├── AI_CONTEXT.md
├── package.json
├── requirements.txt
├── startAll.bat
├── startAll.sh
├── start_backend.bat
└── start_frontend.bat
```

## Current Decisions

- **Multi-Agent Verification Architecture:** 3-Agent pipeline:
  - **Agent 1 (`planner.py`)**: Generates targeted queries for Indian news sources.
  - **Agent 2 (`scraper.py`)**: Scrapes live RSS feeds and filters against whitelisted outlets (PTI, UNI, PIB, TOI, NDTV, etc.).
  - **Agent 3 (`analyzer.py` / `verifier.py`)**: Evaluates evidence against claim and returns structured verdict.
- **Model Fallback Chain:** Automatically tries 10 fallback models (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.0-flash`, `gemini-3-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`) if a model is rate-limited (429), busy (503), or unavailable (404).
- **Session & History Persistence:**
  - Browser state is persisted across page reloads via `sessionStorage`.
  - Backend saves timestamped query execution audit logs in `backend/history_logs/`.
- **Repository Layout Reorganization:** Restructured repository layout into root `backend/`, `frontend/`, and root-level startup scripts (`startAll.bat`, `startAll.sh`, `start_backend.bat`, `start_frontend.bat`), following MediQueue / KingsMove modular standards.

---

## Progress Log

### 2026-09-21 - Repository Reorganization (MediQueue / KingsMove standard)

- Moved application code out of `web_app/` into root `backend/` and `frontend/`.
- Modularized backend:
  - `backend/config/`: App settings, paths, logger, fallback models list.
  - `backend/schemas/`: Pydantic request/response schemas.
  - `backend/utils/`: Progress event emitters.
  - `backend/services/`: History logger and ML model predictor.
  - `backend/agents/`: Agent 1 (Planner), Agent 2 (Scraper), Agent 3 (Analyzer), and `GeminiVerifier`.
  - `backend/controllers/`: Request orchestration controllers.
  - `backend/routes/`: Health & Analyze FastAPI routers.
- Modularized frontend:
  - Split `App.jsx` into `AnalysisForm`, `AnalysisResult`, `SourceList`, `LoadingState`, `ErrorMessage`, `Home` page, and `AnalysisContext`.
  - Added `frontend/src/services/analysisApi.js` API client.
- Added root launcher scripts (`startAll.bat`, `startAll.sh`, `start_backend.bat`, `start_frontend.bat`).
- Updated `README.md`, `backend/README.md`, `frontend/README.md`, `.gitignore`, and `AI_CONTEXT.md`.
