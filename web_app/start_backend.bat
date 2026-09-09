@echo off
title VeriScan Backend API (FastAPI)
echo Starting VeriScan Backend on http://127.0.0.1:8000...
cd /d "%~dp0\.."
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn web_app.backend.main:app --reload --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn web_app.backend.main:app --reload --host 127.0.0.1 --port 8000
)
pause
