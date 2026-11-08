"""Capture real browser screenshot using Chrome DevTools Protocol (CDP)."""

import os
import sys
import time
import json
import base64
import asyncio
import tempfile
import urllib.request
import subprocess
from pathlib import Path
import websockets

ROOT_DIR = Path(__file__).resolve().parent
PY_EXE = str(ROOT_DIR / ".venv" / "Scripts" / "python.exe")
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SHOT_PATH = ROOT_DIR / "frontend" / "assets" / "composer_verified.png"

async def cdp_screenshot(target_url: str, output_path: Path):
    # 1. Fetch CDP target list
    print("Connecting to Chrome CDP at http://127.0.0.1:9222/json...")
    res = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
    targets = json.loads(res.read().decode())
    
    ws_url = None
    for t in targets:
        if t.get("type") == "page":
            ws_url = t.get("webSocketDebuggerUrl")
            break
            
    if not ws_url:
        raise RuntimeError("No page target found in Chrome!")
        
    print(f"Connecting to CDP WebSocket: {ws_url}")
    async with websockets.connect(ws_url, max_size=20*1024*1024) as ws:
        msg_id = 1
        
        async def send_cmd(method, params=None):
            nonlocal msg_id
            mid = msg_id
            msg_id += 1
            cmd = {"id": mid, "method": method, "params": params or {}}
            await ws.send(json.dumps(cmd))
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("id") == mid:
                    return data.get("result", {})

        await send_cmd("Page.enable")
        await send_cmd("DOM.enable")

        print("Waiting for Streamlit dashboard and composer elements to render...")
        for i in range(25):
            await asyncio.sleep(1)
            eval_res = await send_cmd("Runtime.evaluate", {
                "expression": """
                (() => {
                    const chatInput = document.querySelector('[data-testid="stChatInput"]');
                    const popovers = document.querySelectorAll('[data-testid="stPopover"]');
                    const mascot = document.querySelector('.mascot-banner-card');
                    const uploaders = document.querySelectorAll('[data-testid="stFileUploader"]');
                    return {
                        hasChatInput: Boolean(chatInput),
                        popoverCount: popovers.length,
                        hasMascot: Boolean(mascot),
                        uploaderCount: uploaders.length,
                        bodyBg: window.getComputedStyle(document.body).backgroundColor
                    };
                })()
                """,
                "returnByValue": True
            })
            val = eval_res.get("result", {}).get("value", {})
            print(f"      Render status (t={i+1}s): {val}")
            if val.get("hasChatInput") and val.get("hasMascot"):
                print("      Streamlit dashboard and composer elements detected in DOM!")
                break

        # Give 2 seconds for CSS animations/shadows to settle
        await asyncio.sleep(2)

        print(f"Capturing screenshot to {output_path}...")
        shot_res = await send_cmd("Page.captureScreenshot", {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": False
        })
        
        img_b64 = shot_res.get("data", "")
        if img_b64:
            output_path.write_bytes(base64.b64decode(img_b64))
            print(f"Screenshot written successfully! Size: {output_path.stat().st_size} bytes")
        else:
            raise RuntimeError("Failed to capture screenshot data from CDP!")

def main():
    env = {
        **os.environ,
        "USERPROFILE": str(ROOT_DIR),
        "HOME": str(ROOT_DIR),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        "STREAMLIT_SERVER_HEADLESS": "true",
        "PYTHONUNBUFFERED": "1"
    }

    print("[1/5] Starting FastAPI backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [PY_EXE, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("[2/5] Starting Streamlit frontend on http://127.0.0.1:8501...")
    frontend_proc = subprocess.Popen(
        [
            PY_EXE,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--server.enableCORS",
            "false",
            "--server.enableXsrfProtection",
            "false"
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("[3/5] Waiting for backend & frontend...")
    for _ in range(25):
        time.sleep(1)
        try:
            rb = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)
            rf = urllib.request.urlopen("http://127.0.0.1:8501", timeout=2)
            if rb.status == 200 and rf.status == 200:
                print("      Servers online!")
                break
        except Exception:
            pass

    time.sleep(2)

    temp_prof = tempfile.mkdtemp(prefix="chrome_cdp_")
    print(f"[4/5] Launching Chrome in headless CDP mode on port 9222...")
    chrome_proc = subprocess.Popen([
        CHROME_EXE,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,1000",
        f"--user-data-dir={temp_prof}",
        "http://127.0.0.1:8501/?demo=1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for CDP endpoint to be available
        for _ in range(15):
            time.sleep(0.5)
            try:
                urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2)
                break
            except Exception:
                pass

        asyncio.run(cdp_screenshot("http://127.0.0.1:8501/?demo=1", SHOT_PATH))
    finally:
        print("[5/5] Terminating processes...")
        chrome_proc.terminate()
        frontend_proc.terminate()
        backend_proc.terminate()
        chrome_proc.wait()
        frontend_proc.wait()
        backend_proc.wait()

    if SHOT_PATH.exists() and SHOT_PATH.stat().st_size > 10000:
        print(f"SUCCESS! Verified screenshot saved at: {SHOT_PATH} ({SHOT_PATH.stat().st_size} bytes)")
    else:
        print("ERROR: Screenshot file invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
