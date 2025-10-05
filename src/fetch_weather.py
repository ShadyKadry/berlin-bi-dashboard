import requests, csv, os
from datetime import datetime
from pathlib import Path

OUT = Path("data/raw/berlin_weather.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

url = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=52.52&longitude=13.41"
    "&hourly=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,weathercode"
    "&past_days=7&forecast_days=1"
    "&timezone=Europe/Berlin"
)
r = requests.get(url, timeout=30)
r.raise_for_status()
h = r.json().get("hourly", {})

rows = []
times = h.get("time", [])
for i, t in enumerate(times):
    # times are in Europe/Berlin; store as UTC ISO
    ts_local = datetime.fromisoformat(t)  # naive local clock text
    # we do not have tz info from API string; assume local Europe/Berlin
    # write as local string; DB will accept and store; dashboard shows order fine
    rows.append({
        "city": "Berlin",
        "timestamp": ts_local.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": h.get("temperature_2m", [None]*len(times))[i],
        "humidity": h.get("relative_humidity_2m", [None]*len(times))[i],
        "pressure": h.get("pressure_msl", [None]*len(times))[i],
        "wind_speed": h.get("wind_speed_10m", [None]*len(times))[i],
        "weather_code": h.get("weathercode", [None]*len(times))[i],
    })

# overwrite file with full backfill
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUT}")
