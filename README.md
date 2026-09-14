# Fake News Risk Analyzer

A machine learning and NLP project that analyzes news headlines and article text to estimate fake-news likelihood, paired with a modern, distraction-free web interface.

---

## Project Structure

```text
FakeNews/
├── data/                      # Local Kaggle datasets (Fake.csv, True.csv - ignored in git)
├── docs/                      # Project documentation and specifications
│   ├── proposal.html          # Original project proposal document
│   └── source_credibility.md  # News source credibility hierarchy and reference
├── models/                    # Model artifacts (model.joblib - ignored in git)
├── reports/                   # Performance and profiling reports
├── scripts/                   # CLI execution scripts
│   └── train_model.py         # Entry point to train TF-IDF + Logistic Regression model
├── src/                       # Reusable Python package
│   └── fake_news_risk/        # Pipeline builders, dataset loaders, and evaluators
├── web_app/                   # Full-stack interactive web application
│   ├── backend/               # FastAPI REST service
│   ├── frontend/              # React + Vite + Tailwind CSS v4 user interface
│   ├── start_all.bat          # 1-click full-stack launcher
│   ├── start_backend.bat      # Backend launcher
│   ├── start_frontend.bat     # Frontend launcher
│   └── README.md              # Application documentation
├── .gitignore                 # Git ignore rules
├── AI_CONTEXT.md              # Persistent context & decision log for AI agents
└── requirements.txt           # Core ML dependencies
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

To launch both the backend and frontend:
```cmd
web_app\start_all.bat
```
Or run separately:
- **Backend (FastAPI)**: `.venv\Scripts\python.exe -m uvicorn web_app.backend.main:app --reload --host 127.0.0.1 --port 8000`
  - Docs: http://localhost:8000/docs
- **Frontend (React + Vite)**: `cd web_app\frontend && cmd /c npm run dev`
  - UI: http://localhost:5173