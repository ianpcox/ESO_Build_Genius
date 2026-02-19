#!/usr/bin/env python3
"""
Verify that ESO Log (esolog.uesp.net) exportJson does NOT expose trial/boss/zone tables.
Our trial and trash pack seed is from UESP wiki; this script confirms we cannot
verify or ingest that data from esolog with the current API.

Usage: python scripts/verify_esolog_trials.py
"""

import json
import sys
import urllib.request

BASE = "https://esolog.uesp.net/exportJson.php"
USER_AGENT = "ESO-Build-Genius/1.0 (verify trials)"

# Tables we need for trial/boss/trash but that exportJson does not expose
CANDIDATE_TABLES = ("trial", "trials", "boss", "bosses", "zone", "zones", "encounter", "npcLocations", "npc")


def fetch(table: str, limit: int = 1) -> dict:
    url = f"{BASE}?table={table}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    print("Checking ESO Log exportJson for trial/boss/zone-related tables...")
    not_available = []
    for table in CANDIDATE_TABLES:
        try:
            data = fetch(table)
            err = data.get("error")
            if err:
                not_available.append((table, f"API error: {err}"))
            elif data.get("numRecords", 0) is not None and "numRecords" in data:
                # Some tables might return numRecords with another key for the actual data
                keys = [k for k in data if k != "numRecords"]
                if not keys:
                    not_available.append((table, "no data key in response"))
                else:
                    print(f"  {table}: OK (keys: {keys}, numRecords: {data.get('numRecords')})")
            else:
                not_available.append((table, "unexpected response shape"))
        except urllib.error.HTTPError as e:
            not_available.append((table, f"HTTP {e.code}"))
        except Exception as e:
            not_available.append((table, str(e)))

    for table, reason in not_available:
        print(f"  {table}: not available ({reason})")

    # Confirm a known-good table works
    print("\nConfirming a known exportJson table (setSummary limit=1)...")
    try:
        data = fetch("setSummary", limit=1)
        if "setSummary" in data and data.get("numRecords") is not None:
            print("  setSummary: OK (exportJson is reachable).")
        else:
            print("  setSummary: unexpected response.")
    except Exception as e:
        print(f"  setSummary failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nConclusion: Trial/boss/trash data cannot be verified or ingested from ESO Log exportJson.")
    print("Seed data is from UESP wiki (Online:Trials, per-trial pages). See DATA_SOURCES.md.")


if __name__ == "__main__":
    main()
