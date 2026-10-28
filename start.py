"""Unified application runner to start both FastAPI Backend and Streamlit Frontend concurrently."""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 Launching AI Knowledge Assistant (Full-Stack RAG)")
    print("=" * 60)
    print("• Backend API:      http://127.0.0.1:8000 (Swagger: /docs)")
    print("• Frontend UI:      http://127.0.0.1:8501")
    print("• Press Ctrl+C in this window to stop both servers.")
    print("=" * 60)

    # Detect project venv python executable
    root_dir = Path(__file__).resolve().parent
    venv_py_win = root_dir / ".venv" / "Scripts" / "python.exe"
    venv_py_nix = root_dir / ".venv" / "bin" / "python"

    if venv_py_win.exists():
        py_exe = str(venv_py_win)
    elif venv_py_nix.exists():
        py_exe = str(venv_py_nix)
    else:
        py_exe = sys.executable

    print(f"Using Python runtime: {py_exe}")

    backend_proc = subprocess.Popen(
        [py_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    )

    time.sleep(2)

    frontend_proc = subprocess.Popen(
        [py_exe, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "127.0.0.1"]
    )

    def shutdown(sig, frame):
        print("\nStopping services...")
        frontend_proc.terminate()
        backend_proc.terminate()
        frontend_proc.wait()
        backend_proc.wait()
        print("Services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
