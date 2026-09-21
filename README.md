# Fake News Risk Analyzer & Multi-Agent Fact Verifier

A machine learning and multi-agent AI verification project that analyzes news headlines and article text using Gemini LLM fallback chains, live news RSS scraping across trusted Indian news outlets (PTI, UNI, PIB, TOI, NDTV, etc.), and baseline TF-IDF classification pipelines.

---

## Repository Structure

```text
FakeNews/
├── backend/                   # FastAPI backend service & Multi-Agent Pipeline
│   ├── agents/                # Query Planner, News Scraper, Evidence Analyzer
│   ├── config/                # Environment variables & model fallback list
│   ├── controllers/           # Endpoint request controllers
│   ├── routes/                # FastAPI routers (health, analyze)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # History logger & ML predictor services
│   ├── utils/                 # Progress event emitters
│   ├── main.py                # App entry point
│   ├── requirements.txt       # Backend dependencies
│   └── README.md
├── frontend/                  # React + Vite + Tailwind CSS user interface
│   ├── src/
│   │   ├── assets/            # Static image & SVG assets
│   │   ├── components/        # AnalysisForm, AnalysisResult, SourceList, etc.
│   │   ├── context/           # Analysis state & reload persistence
│   │   ├── pages/             # Home page view
│   │   ├── services/          # API fetch client
│   │   ├── App.jsx            # Root composition component
│   │   └── main.jsx           # Entry point
│   ├── package.json
│   └── README.md
├── data/                      # Local datasets (Fake.csv, True.csv - ignored in git)
├── docs/                      # Project documentation and specifications
│   ├── source_credibility.md  # News source credibility hierarchy
│   └── verification_methodology.md
├── models/                    # ML Model artifacts (model.joblib - ignored in git)
├── reports/                   # Performance & profiling reports
├── scripts/                   # Model training execution scripts
│   └── train_model.py         # Entry point to train TF-IDF + Logistic Regression model
├── src/                       # Reusable Python package
│   └── fake_news_risk/        # Pipeline builders, dataset loaders, and evaluators
├── .gitignore                 # Git ignore rules
├── AI_CONTEXT.md              # Project context & decision log
├── package.json               # Root convenience scripts
├── requirements.txt           # Core ML dependencies
├── startAll.bat               # 1-click full-stack launcher (Windows)
├── startAll.sh                # 1-click full-stack launcher (Linux/macOS)
├── start_backend.bat          # Backend launcher
└── start_frontend.bat         # Frontend launcher
```

---

## Setup & Training

### 1. Python Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Train Model
```powershell
python scripts/train_model.py
```
The trainer loads `data/Fake.csv` and `data/True.csv`, builds a TF-IDF vectorizer + Logistic Regression pipeline, evaluates on a stratified 20% test split, and outputs `models/model.joblib` and `reports/performance_report.json`.

---

## Running the Web Application

### Option A: 1-Click Launchers
- **Windows**: Double-click `startAll.bat`
- **Linux/macOS**: `bash startAll.sh`

### Option B: Separate Launchers
- **Backend (FastAPI)**:
  ```powershell
  python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
  ```
  - API Specs: http://localhost:8000/docs
- **Frontend (React)**:
  ```powershell
  cd frontend
  npm run dev
  ```
  - Web UI: http://localhost:5173