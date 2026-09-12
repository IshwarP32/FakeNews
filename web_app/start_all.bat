@echo off
title Launch VeriScan Full Stack
echo Starting VeriScan Backend and Frontend...
start "VeriScan Backend" "%~dp0start_backend.bat"
timeout /t 2 >nul
start "VeriScan Frontend" "%~dp0start_frontend.bat"
echo Both servers started!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://localhost:8000/docs
