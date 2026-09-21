@echo off
title FakeNews Application Launcher
echo Launching FakeNews Backend and Frontend...
start "FakeNews Backend" cmd /k "%~dp0start_backend.bat"
start "FakeNews Frontend" cmd /k "%~dp0start_frontend.bat"
echo Applications launched. Close the opened terminal windows to stop.
