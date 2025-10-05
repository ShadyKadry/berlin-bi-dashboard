import runpy
import os
import sys
import subprocess
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ---------- Config / DB ----------
st.set_page_config(
    page_title="Berlin Weather BI",
    layout="wide",
    initial_sidebar_state="expanded"   # <-- keep sidebar open
)

load_dotenv()  # reads .env if present

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5433")
PGUSER = os.getenv("PGUSER", "shady")
PGPASSWORD = os.getenv("PGPASSWORD", "shady")
PGDATABASE = os.getenv("PGDATABASE", "berlin_bi")

engine = create_engine(
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
)

# ---------- Helpers ----------
from pathlib import Path
import sys

def _find_script(*names: str) -> Path:
    """
    Find a script whether running from source or a PyInstaller build.

    We try several roots:
      - folder containing this file (often .../_internal in onedir)
      - its parent (the app root in onedir)
      - current working directory
      - folder of the running executable (EXE)
      - PyInstaller temp dir (onefile), if present
      - plus each of those with a trailing /src
    """
    here = Path(__file__).resolve()
    roots = [
        here.parent,                          # _internal (onedir)
        here.parent.parent,                   # app root (onedir)
        Path.cwd(),                           # current working dir
        Path(sys.executable).parent,          # EXE folder
        Path(getattr(sys, "_MEIPASS", here)), # onefile temp, else fallback
    ]

    candidates = []
    for n in names:
        for r in roots:
            candidates.append(r / n)
            candidates.append(r / "src" / n)

    for p in candidates:
        if p.is_file():
            return p

    raise FileNotFoundError(f"Could not find any of: {', '.join(names)}\nSearched:\n" +
                           "\n".join(str(c) for c in candidates[:12]) + ("\n..."))


@st.cache_data(ttl=300)
def load_weather() -> pd.DataFrame:
    return pd.read_sql(
        """
        SELECT city, ts, temperature, humidity, pressure, wind_speed, weather_code
        FROM weather
        ORDER BY ts
        """,
        engine,
        parse_dates=["ts"],
    )

@st.cache_data(ttl=300)
def load_daily() -> pd.DataFrame:
    try:
        return pd.read_sql(
            "SELECT day, avg_temp, min_temp, max_temp, avg_humidity FROM weather_daily ORDER BY day",
            engine,
            parse_dates=["day"],
        )
    except Exception:
        # table might not exist yet
        return pd.DataFrame(columns=["day", "avg_temp", "min_temp", "max_temp", "avg_humidity"])

def do_update():
    """Fetch + upsert, clear caches, rerun."""
    try:
        fetch_path = _find_script("fetch_weather.py")
        load_path  = _find_script("load_to_postgres.py")
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    is_frozen = getattr(sys, "frozen", False)

    # ---- Step 1: fetch -> CSV
    with st.spinner("Fetching latest weather data…"):
        if is_frozen:
            # run the script inside this Python process
            try:
                runpy.run_path(str(fetch_path), run_name="__main__")
                st.success("Fetch OK")
            except Exception as e:
                st.error("Fetch failed.")
                st.exception(e)
                st.stop()
        else:
            p1 = subprocess.run([sys.executable, str(fetch_path)], capture_output=True, text=True)
            if p1.returncode != 0:
                st.error("Fetch failed.")
                st.code(p1.stderr or p1.stdout)
                st.stop()
            st.success("Fetch OK")
            if p1.stdout:
                st.code(p1.stdout.strip())

    # ---- Step 2: upsert -> Postgres
    with st.spinner("Upserting into PostgreSQL…"):
        if is_frozen:
            try:
                runpy.run_path(str(load_path), run_name="__main__")
                st.success("Upsert OK")
            except Exception as e:
                st.error("Upsert failed.")
                st.exception(e)
                st.stop()
        else:
            p2 = subprocess.run([sys.executable, str(load_path)], capture_output=True, text=True)
            if p2.returncode != 0:
                st.error("Upsert failed.")
                st.code(p2.stderr or p2.stdout)
                st.stop()
            st.success("Upsert OK")
            if p2.stdout:
                st.code(p2.stdout.strip())

    # Clear caches and refresh UI
    st.cache_data.clear()
    st.toast("Data updated. Refreshing…", icon="✅")
    st.rerun()


# ---------- Sidebar: Update button ----------
with st.sidebar:
    st.markdown("### Data control")
    if st.button("🔄 Update data now", use_container_width=True):
        do_update()

# ---------- Main: Top Update button (duplicate for convenience) ----------
top_left, _ = st.columns([1, 6])
with top_left:
    if st.button("🔄 Update data now (main)"):
        do_update()

# ---------- Main App ----------
st.title("Berlin Weather - BI Snapshot")

df = load_weather()

if df.empty:
    st.warning("No data yet. Click **Update data now** (sidebar or top).")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Records", len(df))
    c2.metric("Last temp (°C)", f"{df['temperature'].iloc[-1]:.1f}")
    c3.metric("Last humidity (%)", f"{int(df['humidity'].iloc[-1])}")

    st.plotly_chart(px.line(df, x="ts", y="temperature", title="Temperature (°C)"), use_container_width=True)
    st.plotly_chart(px.line(df, x="ts", y="humidity", title="Humidity (%)"), use_container_width=True)

    st.subheader("Latest rows")
    st.dataframe(df.tail(10), use_container_width=True)

daily = load_daily()
st.subheader("Daily summary (last 7–8 days)")
if not daily.empty:
    st.line_chart(daily.set_index("day")[["avg_temp"]])
    st.dataframe(daily.tail(10), use_container_width=True)
else:
    st.info("No daily summary yet. It will appear after an update once the materialized view is created/refreshed.")
