@echo off
echo ========================================================
echo Starting AI Knowledge Assistant - FastAPI Backend (8000)
echo ========================================================
call .venv\Scripts\activate.bat
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
