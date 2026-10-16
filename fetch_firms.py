"""Download VIIRS hotspots from NASA FIRMS for northern Algeria and save them as a CSV.

Same sources, box, columns and filter as FindFire_zones_tracking_replay.ipynb.

Usage:
    export FIRMS_MAP_KEY=your_key_here          # never hard-code or commit the key
    python fetch_firms.py --start 2021-08-08 --end 2021-08-14
    python fetch_firms.py --start 2025-08-01 --end 2025-08-10 --source VIIRS_SNPP_NRT,VIIRS_NOAA20_NRT

Sources (comma-separated):
    *_SP   standard processing (archive): use for past events and training / validation
    *_NRT  near real time (about 3 hours after the pass): use for recent data
    e.g. VIIRS_SNPP_SP, VIIRS_NOAA20_SP, VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT
NOAA-20 observes within about an hour of Suomi NPP, so one fire can appear twice (see the notebook).
"""
import argparse
import datetime as dt
import io
import os
import time

import pandas as pd
import requests

BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
BBOX = (-2.0, 34.0, 8.5, 37.5)        # west, south, east, north (northern Algeria), same as the notebook
MAX_DAYS = 5                          # API limit per request
DEFAULT_SOURCES = "VIIRS_SNPP_SP,VIIRS_NOAA20_SP"


def fetch_chunk(key, source, start, days):
    w, s, e, n = BBOX
    url = f"{BASE}/{key}/{source}/{w},{s},{e},{n}/{days}/{start:%Y-%m-%d}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            text = r.text.strip()
            if not text.startswith("latitude"):
                raise RuntimeError(f"Unexpected response: {text[:200]}")
            return pd.read_csv(io.StringIO(text))
        except (requests.RequestException, RuntimeError) as exc:
            print(f"  retry {attempt + 1} for {source} {start:%Y-%m-%d}: {exc}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {source} chunk starting {start:%Y-%m-%d}")


def fetch_firms(key, sources, start, end):
    """Download every source for the date range and stack them. A failing source is skipped with a warning."""
    frames = []
    for source in sources:
        try:
            cur = start
            while cur <= end:
                days = min(MAX_DAYS, (end - cur).days + 1)
                print(f"{source}: {cur:%Y-%m-%d} (+{days} d)")
                part = fetch_chunk(key, source, cur, days)
                part["source"] = source
                frames.append(part)
                cur += dt.timedelta(days=days)
                time.sleep(1)                      # be polite; limit is ~5000 requests / 10 min
        except Exception as exc:
            print(f"warning: {source} skipped ({exc})")
    if not frames:
        raise RuntimeError("no data downloaded from any source")
    return pd.concat(frames, ignore_index=True).drop_duplicates()


def prepare(raw):
    """Same cleaning as the notebook: UTC timestamp, drop low confidence, keep scan / track (pixel size, km)."""
    d = raw.copy()
    d["acq_dt"] = pd.to_datetime(d["acq_date"] + " " + d["acq_time"].astype(int).astype(str).str.zfill(4),
                                 format="%Y-%m-%d %H%M", utc=True)
    d = d[d["confidence"].astype(str).str.lower() != "l"]
    return d.sort_values("acq_dt").reset_index(drop=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, type=dt.date.fromisoformat)
    p.add_argument("--end", required=True, type=dt.date.fromisoformat)
    p.add_argument("--source", default=DEFAULT_SOURCES, help="comma-separated FIRMS sources")
    p.add_argument("--out", default="hotspots.csv")
    a = p.parse_args()

    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        raise SystemExit("Set the FIRMS_MAP_KEY environment variable first.")
    df = prepare(fetch_firms(key, [s.strip() for s in a.source.split(",") if s.strip()], a.start, a.end))
    df.to_csv(a.out, index=False)
    print(f"Saved {len(df)} hotspots to {a.out}")


if __name__ == "__main__":
    main()
