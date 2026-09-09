# VeriScan - Fake News Risk Analyzer (Full-Stack Web App)

A modern full-stack web application designed for explainable misinformation risk evaluation. It pairs a trained scikit-learn TF-IDF + Logistic Regression machine learning model with heuristic feature analysis (sensationalism, urgency cues, formatting/capitalization anomalies, and attribution verification).

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

- **Trained NLP Classification**: Loads `models/model.joblib` to calculate fake vs. real probability.
- **Sensationalism & Clickbait Detection**: Scans for emotionally charged clickbait phrases and buzzwords.
- **Urgency & Alarmism Profiling**: Detects panic words and crisis triggers.
- **Stylistic & Formatting Analysis**: Identifies abnormal all-caps words, repeated punctuation (`!!`, `???`), and capitalization ratios.
- **Attribution & Credibility Scoring**: Identifies journalistic citations, official quotes, and reputable source mentions.
- **Composite 0–100% Risk Score**: Synthesizes all signals into an explainable score and level (`Low Risk`, `Moderate Risk`, `High Risk`, `Critical Risk`).
- **One-Click Test Presets**: Includes preloaded real news and viral fake stories for fast testing.
- **Session History Log**: Keeps track of recent analyses during your session.

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

#### 2. Frontend (React + Vite)
```powershell
cd web_app\frontend
cmd /c npm run dev
```
- Web Application: http://localhost:5173
