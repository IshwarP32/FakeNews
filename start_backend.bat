@echo off
title FakeNews Backend API (FastAPI)
echo Starting FakeNews Backend on http://127.0.0.1:8000...
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
)
pause
