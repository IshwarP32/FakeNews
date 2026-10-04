@echo off
title FakeNews Test Launcher
cd /d "%~dp0"
echo Launching FakeNews Backend and Frontend for testing...

if exist ".venv\Scripts\python.exe" (
	start "FakeNews Backend" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
) else (
	start "FakeNews Backend" cmd /k "python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
)

start "FakeNews Frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"
echo Applications launched. Close the opened terminal windows to stop testing.
