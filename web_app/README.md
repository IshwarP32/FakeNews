# VeriScan - Fake News Risk Analyzer (Full-Stack Web App)

A modern full-stack web application designed for India-focused, evidence-based news verification. The active workflow uses Gemini to plan searches, fetches direct PTI and UNI pages, and asks Gemini to compare the evidence. The previous scikit-learn model remains dormant for now.

---

## Project Structure

```
FakeNews/
├── web_app/
│   ├── backend/
│   │   ├── main.py             # FastAPI REST server with CORS & endpoints
│   │   ├── analyzer.py         # Multi-factor RiskAnalyzer engine
│   │   └── requirements.txt    # Backend dependencies
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx         # Interactive React UI with risk meters & presets
│   │   │   ├── App.css         # Component styling & dark glassmorphism
│   │   │   ├── index.css       # Global design system & theme tokens
│   │   │   └── main.jsx        # React entry point
│   │   ├── vite.config.js      # Vite config with API proxy to port 8000
│   │   └── package.json        # Frontend dependencies (React + Lucide icons)
│   ├── start_backend.bat       # Quick launch for Python FastAPI server
│   ├── start_frontend.bat      # Quick launch for React Vite dev server
│   └── start_all.bat           # Launch both backend and frontend together
```

---

## Features

- **PTI/UNI Research**: Treats the pasted headline or article as a claim and searches PTI and UNI independently for reporting about that topic.
- **Separate Scrapers**: Keeps PTI and UNI logic in `pti_scraper.py` and `uni_scraper.py`, coordinated by `source_research.py`.
- **Gemini Query Planning**: Generates up to three alternative queries per source so different wording, names, and relevant details are less likely to miss matching reports.
- **Direct Source Fetching**: Uses Google News only for discovery, decodes the result, validates the PTI/UNI hostname, and fetches publisher HTML before returning evidence.
- **Gemini Evidence Verdict**: Returns `True`, `False`, `Partially True`, or `Unverified`, with confidence, reasoning, corrected news, and source references.
- **Live Progress Stream**: `POST /api/analyze/stream` returns Server-Sent Events for query planning, source retrieval, evidence collection, verification, and completion. Backend events are timestamped in the `fake_news_risk` logger and mirrored in the frontend timeline and browser console.

---

## How to Run

### Option 1: Quick Launch (Windows Batch Scripts)
Double-click `web_app/start_all.bat` or run:
```cmd
web_app\start_all.bat
```

### Option 2: Run Separately

#### 1. Backend (FastAPI)
```powershell
# From the project root:
.venv\Scripts\python.exe -m uvicorn web_app.backend.main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs (Swagger): http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
- Streaming analysis: `POST http://localhost:8000/api/analyze/stream` (the only analysis endpoint)

#### 2. Frontend (React + Vite)
```powershell
cd web_app\frontend
cmd /c npm run dev
```
- Web Application: http://localhost:5173
