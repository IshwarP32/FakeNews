# Fake News Verifier - FastAPI Backend Service

This service provides real-time news claim verification powered by a **Multi-Agent AI Pipeline** using Gemini and date-windowed Google News RSS retrieval across Indian news agencies and official sources.

## Directory Structure

```
backend/
├── agents/                  # Multi-Agent Pipeline
│   ├── planner.py           # Agent 1: Structured claim analysis and query plan
│   ├── scraper.py           # Agent 2: Date-windowed candidate retrieval/ranking
│   ├── analyzer.py          # Agent 3: Structured evidence validation
│   └── verifier.py          # Pipeline Orchestrator (GeminiVerifier)
├── config/                  # Settings, base paths, and model fallback list
│   ├── settings.py
│   ├── prompts.py
│   └── sources.yaml         # Editable source credibility tiers
├── controllers/             # Controller logic for endpoints
│   └── analyze_controller.py
├── routes/                  # API Routers
│   ├── health.py            # GET /api/health
│   └── analyze.py           # POST /api/analyze & POST /api/analyze/stream
├── schemas/                 # Pydantic request/response schemas
│   └── analyze.py
├── services/                # Supporting services (History logging)
│   ├── history.py           # Timestamped query history logger
├── utils/                   # Shared utilities & progress event emitters
│   └── progress.py
├── main.py                  # FastAPI application entry point
└── requirements.txt         # Dependencies
```

## API Endpoints

- `GET /api/health`: Health check endpoint.
- `POST /api/analyze`: Non-streaming news claim verification endpoint.
- `POST /api/analyze/stream`: Server-Sent Events (SSE) streaming endpoint for live agent execution progress.

Responses use `schema_version: "2.0"` and contain the validated `verdict`, separate `evidence_articles` and `context_articles`, and a `coverage` block. The frontend never displays articles that fail code-side ID, relevance, or quote validation.

## Setup & Running

1. Ensure environment variables are configured in `.env` at root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-3.6-flash
   ```

## Deployment

See [`docs/AUDIT.md`](../docs/AUDIT.md) for the failure-mode audit and [`docs/deployment.md`](../docs/deployment.md) for Render/Vercel setup.

Run deterministic evidence validation fixtures with:

```powershell
.venv\Scripts\python.exe eval\run.py
```

2. Start the FastAPI server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
