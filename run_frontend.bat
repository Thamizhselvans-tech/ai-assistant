@echo off
echo ========================================================
echo Starting AI Knowledge Assistant - Streamlit Frontend (8501)
echo ========================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1
) else (
    python -m streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1
)
pause
