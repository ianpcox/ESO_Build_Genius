#!/usr/bin/env python3
"""
Verify that skills for the Update 48 (Patch 48) game build match the UESP ESO Log skillCoef count.

Queries the DB for the build labeled "Update 48" and counts skills, then fetches the
skillCoef API to get the expected record count and compares.

Usage:
  python scripts/check_skills_patch48.py [--db PATH] [--build-label "Update 48"]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "eso_build_genius.db")
UESP_SKILL_COEF_URL = "https://esolog.uesp.net/exportJson.php"
USER_AGENT = "ESO-Build-Genius/1.0 (https://github.com/)"
CHUNK_SIZE = 2000
# Expected skillCoef size (~7083 per viewSkillCoef). Outside range suggests wrong table or API change.
EXPECTED_SKILL_COEF_MIN = 5000
EXPECTED_SKILL_COEF_MAX = 12000


def fetch_skill_coef_count() -> int:
    """Fetch total skillCoef record count from UESP via pagination (API numRecords is per-response)."""
    total = 0
    offset = 0
    while True:
        url = f"{UESP_SKILL_COEF_URL}?table=skillCoef&limit={CHUNK_SIZE}&offset={offset}"
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=120) as resp:
            data = json.load(resp)
        chunk = data.get("skillCoef") or []
        total += len(chunk)
        if len(chunk) < CHUNK_SIZE:
            break
        offset += len(chunk)
        time.sleep(0.3)
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify Patch 48 skill count vs UESP skillCoef")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-label", default="Update 48", help="Game build label")
    ap.add_argument("--skip-fetch", action="store_true", help="Do not call UESP API; only report DB counts")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    row = conn.execute(
        "SELECT id FROM game_builds WHERE label = ?",
        (args.build_label,),
    ).fetchone()
    if not row:
        print(f"No game_build with label {args.build_label!r} in DB.", file=sys.stderr)
        conn.close()
        return 1

    game_build_id = row[0]
    total_skills = conn.execute(
        "SELECT COUNT(*) FROM skills WHERE game_build_id = ?",
        (game_build_id,),
    ).fetchone()[0]
    with_coef = conn.execute(
        "SELECT COUNT(*) FROM skills WHERE game_build_id = ? AND coefficient_json IS NOT NULL AND coefficient_json != ''",
        (game_build_id,),
    ).fetchone()[0]
    from_uesp = conn.execute(
        "SELECT COUNT(*) FROM skills WHERE game_build_id = ? AND data_source = 'esolog_skillCoef'",
        (game_build_id,),
    ).fetchone()[0]
    conn.close()

    print(f"Build: {args.build_label!r} (game_build_id={game_build_id})")
    print(f"  Skills in DB:           {total_skills:,}")
    print(f"  With coefficient_json:  {with_coef:,}")
    print(f"  data_source=esolog_skillCoef: {from_uesp:,}")

    if args.skip_fetch:
        print("\n(Skipping UESP API fetch; use without --skip-fetch to compare to source.)")
        return 0

    print("\nFetching UESP skillCoef total ...")
    try:
        expected = fetch_skill_coef_count()
    except Exception as e:
        print(f"UESP API error: {e}", file=sys.stderr)
        return 1

    print(f"  UESP skillCoef records: {expected:,}")
    if expected < EXPECTED_SKILL_COEF_MIN or expected > EXPECTED_SKILL_COEF_MAX:
        print(f"  WARNING: UESP count outside expected range {EXPECTED_SKILL_COEF_MIN}-{EXPECTED_SKILL_COEF_MAX}. API or table may have changed.", file=sys.stderr)
    if total_skills > EXPECTED_SKILL_COEF_MAX and from_uesp > EXPECTED_SKILL_COEF_MAX:
        print(f"  WARNING: DB has {total_skills:,} skills (expected ~7k). Possible minedSkills ingest; pipeline expects skillCoef only.", file=sys.stderr)
    if total_skills >= expected and from_uesp >= expected:
        print("\n  OK: DB has at least as many skillCoef-sourced rows as UESP (~Patch 48 current).")
    elif total_skills < expected:
        print(f"\n  GAP: DB has {total_skills:,} skills, UESP has {expected:,}. Run: python scripts/ingest_skills_uesp.py --build-label \"Update 48\" --replace")
        return 1
    else:
        print("\n  OK: DB skill count meets or exceeds UESP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
