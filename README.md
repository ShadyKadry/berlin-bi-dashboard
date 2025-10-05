# Berlin Weather BI Dashboard

A small end-to-end analytics stack that:

- **Fetches** hourly weather for Berlin into CSV  
- **Upserts** that CSV into **PostgreSQL** (Docker)  
- **Visualizes** it in a **Streamlit** dashboard  
- Provides a one-click **“Update data now”** button inside the app  
- Can be packaged into a **Windows .exe** launcher

---

## Table of Contents

- [Demo & Features](#demo--features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start (Run from Source)](#quick-start-run-from-source)
- [Environment Variables](#environment-variables)
- [Data Ingestion](#data-ingestion)
- [Run the Dashboard](#run-the-dashboard)
- [Build & Run the Windows EXE (Optional)](#build--run-the-windows-exe-optional)
- [Database Schema & Constraints](#database-schema--constraints)
- [Scheduling Automatic Updates (Optional)](#scheduling-automatic-updates-optional)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Git Hygiene / What Not to Commit](#git-hygiene--what-not-to-commit)
- [Contributing](#contributing)
- [License](#license)

---

## Demo & Features

**What you get**
- 📥 Fetch hourly weather data to `data/raw/berlin_weather.csv`
- 🧩 Load/Upsert into Postgres with a **true upsert** on `(city, ts)` (no duplicates)
- 📊 Streamlit dashboard (line charts + table)
- 🔄 **Update data now** button (runs fetch → load → clear cache → refresh)
- 🪟 Windows **EXE** build that opens your browser (default `http://localhost:8503`) and runs the app without the CLI

---

## Architecture Overview

- **Data source** → `src/fetch_weather.py`  
  Fetches weather for Berlin and writes a normalized CSV.

- **Storage** → Dockerized **PostgreSQL**  
  `docker-compose.yml` maps **host 5433 → container 5432**.

- **Ingest/Upsert** → `src/load_to_postgres.py`  
  Reads CSV, normalizes timestamps, and executes an **INSERT … ON CONFLICT DO UPDATE** keyed on `(city, ts)`.

- **Visualization** → `src/app_streamlit.py`  
  Connects to Postgres, draws charts/tables, and exposes an **Update** button that runs the ingestion scripts.

- **Packaging** → `src/run_dashboard.py` (+ PyInstaller)  
  Launcher that runs Streamlit at a fixed port and opens your browser.

---

## Project Structure

berlin-bi-dashboard/
├─ docker-compose.yml # Postgres (host 5433 -> container 5432)
├─ requirements.txt # Python dependencies
├─ .env.sample # Example env vars (copy to .env)
├─ src/
│ ├─ fetch_weather.py # Fetch hourly weather -> CSV
│ ├─ load_to_postgres.py # Upsert CSV -> Postgres (UNIQUE(city, ts))
│ ├─ app_streamlit.py # Streamlit app + “Update data now” buttons
│ └─ run_dashboard.py # Windows launcher used for EXE packaging
└─ data/
└─ raw/berlin_weather.csv # Latest fetched data (gitignored)


---

## Prerequisites

- **Windows 10/11**
- **Docker Desktop**
- **Python 3.11–3.13** (with `pip` & `venv`)
- (Optional) **PyInstaller** (to build the .exe)

> Commands below use **PowerShell**. On macOS/Linux, adapt paths and slashes.

---

## Quick Start (Run from Source)

1. **Clone & enter**
   ```powershell
   git clone https://github.com/<your-username>/berlin-bi-dashboard.git
   cd berlin-bi-dashboard
2. **Create & activate a virtualenv**
   python -m venv venv
   .\venv\Scripts\activate
3. **Install dependencies**
   pip install -r requirements.txt
4. **Start Postgres (Docker)**
   docker compose up -d
   Postgres will be available on localhost:5433 (mapped to container 5432).
   If 5433 is busy, change the left side of the mapping in docker-compose.yml and also update your .env (see next section).
5. **Copy environment sample → .env (recommended)**
   Copy-Item .env.sample .env
6. **Fetch & load data (first run)**
   python .\src\fetch_weather.py       # writes data\raw\berlin_weather.csv
   python .\src\load_to_postgres.py    # upserts into Postgres (idempotent)
7. **Run the dashboard**
   python -m streamlit run .\src\app_streamlit.py

## Environment Variables
Create a .env in the repo root (these are the defaults; see .env.sample):
PGHOST=localhost
PGPORT=5433
PGUSER=shady
PGPASSWORD=shady
PGDATABASE=berlin_bi

Both the app and the loader read .env via python-dotenv.
If you change the Docker port mapping, update PGPORT here.

## Data Ingestion Details
1- src/fetch_weather.py

Fetches recent hourly weather and writes data/raw/berlin_weather.csv.

Output columns:

city

ts (UTC timestamp)

temperature, humidity, pressure, wind_speed, weather_code

2- src/load_to_postgres.py

Reads data/raw/berlin_weather.csv.

Converts timestamp column to UTC ts.

Ensures required columns exist.

Executes UPSERT: INSERT … ON CONFLICT (city, ts) DO UPDATE ….

Re-running is safe — new rows insert; existing rows update.

##Run the Dashboard
From the project root:
.\venv\Scripts\activate
python -m streamlit run .\src\app_streamlit.py


## Update buttons (sidebar + top):

Run fetch_weather.py → refresh CSV

Run load_to_postgres.py → upsert DB

Clear Streamlit caches

Rerun the app (charts refresh)

## Build and run the windows .EXE (optional)    

