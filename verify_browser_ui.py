"""Automated real browser verification script for AI Knowledge Assistant UI."""

import os
import sys
import time
import subprocess
import tempfile
import urllib.request
from pathlib import Path

def main():
    root_dir = Path(__file__).resolve().parent
    py_exe = str(root_dir / ".venv" / "Scripts" / "python.exe")
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    shot_path = root_dir / "frontend" / "assets" / "composer_verified.png"

    env = {
        **os.environ,
        "USERPROFILE": str(root_dir),
        "HOME": str(root_dir),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        "STREAMLIT_SERVER_HEADLESS": "true",
        "PYTHONUNBUFFERED": "1"
    }

    print("[1/5] Starting FastAPI backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [py_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("[2/5] Starting Streamlit frontend on http://127.0.0.1:8501...")
    frontend_proc = subprocess.Popen(
        [
            py_exe,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true"
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for services to be ready
    print("[3/5] Waiting for services to become ready...")
    ready = False
    for attempt in range(25):
        time.sleep(1)
        try:
            req_b = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)
            req_f = urllib.request.urlopen("http://127.0.0.1:8501", timeout=2)
            if req_b.status == 200 and req_f.status == 200:
                print(f"      Backend and Frontend both READY! (attempt {attempt+1})")
                ready = True
                break
        except Exception:
            pass

    if not ready:
        print("ERROR: Timed out waiting for servers to start.")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(1)

    # Wait 3 extra seconds for Streamlit frontend app scripts to compile and render
    time.sleep(3)

    # Take screenshot using headless Chrome
    print(f"[4/5] Capturing browser screenshot to {shot_path}...")
    temp_prof = tempfile.mkdtemp(prefix="chrome_shot_")
    chrome_cmd = [
        chrome_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,950",
        "--virtual-time-budget=10000",
        "--run-all-compositor-stages-before-draw",
        f"--user-data-dir={temp_prof}",
        f"--screenshot={shot_path}",
        "http://127.0.0.1:8501/?demo=1"
    ]

    subprocess.run(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)

    # Terminate background services
    print("[5/5] Shutting down services...")
    frontend_proc.terminate()
    backend_proc.terminate()
    frontend_proc.wait()
    backend_proc.wait()

    if shot_path.exists() and shot_path.stat().st_size > 5000:
        print(f"SUCCESS: Screenshot captured successfully! Size: {shot_path.stat().st_size} bytes")
        print(f"Saved at: {shot_path}")
    else:
        print(f"ERROR: Screenshot failed or file too small: {shot_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
