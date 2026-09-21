# Fake News Verifier - FastAPI Backend Service

This service provides real-time news claim verification powered by a **Multi-Agent AI Pipeline** using Gemini and RSS search feeds across trusted Indian news agencies (PTI, UNI, PIB, TOI, NDTV, etc.).

## Directory Structure

```
backend/
├── agents/                  # Multi-Agent Pipeline
│   ├── planner.py           # Agent 1: Search Query Planner
│   ├── scraper.py           # Agent 2: Live News RSS Scraper
│   ├── analyzer.py          # Agent 3: Evidence Analyzer & Fact Verifier
│   └── verifier.py          # Pipeline Orchestrator (GeminiVerifier)
├── config/                  # Settings, base paths, and model fallback list
│   └── settings.py
├── controllers/             # Controller logic for endpoints
│   └── analyze_controller.py
├── routes/                  # API Routers
│   ├── health.py            # GET /api/health
│   └── analyze.py           # POST /api/analyze & POST /api/analyze/stream
├── schemas/                 # Pydantic request/response schemas
│   └── analyze.py
├── services/                # Supporting services (History logging, ML predictor)
│   ├── history.py           # Timestamped query history logger
│   └── ml_predictor.py      # Joblib ML model prediction baseline
├── utils/                   # Shared utilities & progress event emitters
│   └── progress.py
├── main.py                  # FastAPI application entry point
└── requirements.txt         # Dependencies
```

## API Endpoints

- `GET /api/health`: Health check endpoint.
- `POST /api/analyze`: Non-streaming news claim verification endpoint.
- `POST /api/analyze/stream`: Server-Sent Events (SSE) streaming endpoint for live agent execution progress.

## Setup & Running

1. Ensure environment variables are configured in `.env` at root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-3.6-flash
   ```

2. Start the FastAPI server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
