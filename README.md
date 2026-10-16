# FindFire

Satellite fire detections for northern Algeria, grouped into fire zones, tracked over time and shown on a map.
An optional phase 2 matches early alerts from the geostationary MTG satellite to the VIIRS zones.

## Setup
    pip install -r requirements.txt
    export FIRMS_MAP_KEY=your_key_here        # NASA FIRMS key, never commit it (use a .env file that git ignores)

## Files
| File | What it is |
|---|---|
| `FindFire_zones_tracking_replay.ipynb` | Main pipeline: fetch VIIRS, group into zones, track, interactive map, JSON export |
| `FindFire_phase2_alerts.ipynb` | Phase 2: MTG alerts matched to VIIRS zones, lead time, metrics. Runs the main notebook first if needed |
| `fetch_firms.py` | Command line download of the same VIIRS data to a CSV |
| `findfire_alerts.py`, `test_findfire_alerts.py` | The phase 2 functions as a module, and their tests (`pytest`) |
| `FindFire_Project_Plan.pdf` | The project plan |

## Run order
1. Open `FindFire_zones_tracking_replay.ipynb`, set `START`, `END` and `EVENT` in the first cell, run all cells.
   Without `FIRMS_MAP_KEY` (or without internet) it runs on clearly labelled synthetic demo data.
2. Optional: open `FindFire_phase2_alerts.ipynb` and run all cells. It is a dry run on fake detections until you set `MTG_CSV`.

## Notes
- The map tiles (Esri) load from the internet. OpenStreetMap's own servers block notebook requests.
- Two VIIRS satellites are used by default, so a fire can be counted twice in `n_hotspots` and `frp_total_mw`. Areas are not affected.
- All times in the files are UTC. The map shows Algerian local time (UTC+1).
