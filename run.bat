@echo off
title AI Prompt-to-Video Studio
echo ===================================================
echo     Launching AI Prompt-to-Video Studio
echo ===================================================
echo.
cd /d "%~dp0"
echo Starting FastAPI Web Server at http://127.0.0.1:8000 ...
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause
