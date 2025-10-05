# src/run_dashboard.py
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

def app_path() -> Path:
    # When frozen by PyInstaller, app lives under _MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app_streamlit.py"
    return Path(__file__).parent / "app_streamlit.py"

app = app_path()
if not app.exists():
    raise FileNotFoundError(f"app_streamlit.py not found at: {app}")

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8503")
threading.Thread(target=open_browser, daemon=True).start()

try:
    try:
        from streamlit.web.cli import main as st_main
    except Exception:
        from streamlit.cli import main as st_main

    sys.argv = [
        "streamlit", "run", str(app),
        "--global.developmentMode=false",
        "--server.port=8503",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
    ]
    st_main()
except SystemExit:
    raise
