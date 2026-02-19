#!/usr/bin/env python3
"""
Verify class skill lines from ESO Log (esolog.uesp.net) playerSkills against our
skill_lines seed. Used for subclassing: ensures our class_id and skill_line_id
match the game data (classType -> classes, skillLine -> skill_lines name).

Usage:
  python scripts/verify_skill_lines_esolog.py [--db PATH] [--build-label "Update 48"]
  python scripts/verify_skill_lines_esolog.py --limit 500
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
DEFAULT_DB = os.path.join(ROOT_DIR, "data", "eso_build_genius.db")
BASE_URL = "https://esolog.uesp.net/exportJson.php"
USER_AGENT = "ESO-Build-Genius/1.0"
CHUNK = 2000


def fetch_player_skills(limit: int | None, offset: int = 0) -> list[dict]:
    url = f"{BASE_URL}?table=playerSkills&limit={min(CHUNK, limit or CHUNK)}&offset={offset}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data.get("playerSkills") or []


def collect_class_lines_from_esolog(limit: int | None) -> set[tuple[str, str]]:
    """(classType, skillLine) for player skills that have both (class skill lines)."""
    seen: set[tuple[str, str]] = set()
    offset = 0
    while True:
        chunk = fetch_player_skills(limit and (limit - len(seen)), offset)
        if not chunk:
            break
        for rec in chunk:
            ct = (rec.get("classType") or "").strip()
            sl = (rec.get("skillLine") or "").strip()
            if ct and sl:
                seen.add((ct, sl))
        if limit and len(seen) >= limit:
            break
        if len(chunk) < CHUNK:
            break
        offset += len(chunk)
        time.sleep(0.3)
    return seen


def load_db_class_lines(conn: sqlite3.Connection, game_build_id: int) -> list[tuple[int, str, int, str]]:
    """(class_id, class_name, skill_line_id, skill_line_name) for type='class'."""
    return conn.execute(
        """
        SELECT c.id, c.name, s.skill_line_id, s.name
        FROM skill_lines s
        JOIN classes c ON c.id = s.class_id
        WHERE s.game_build_id = ? AND s.skill_line_type = 'class'
        ORDER BY c.id, s.skill_line_id
        """,
        (game_build_id,),
    ).fetchall()


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify class skill lines from ESO Log vs DB seed")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-label", default="Update 48", help="Game build label (e.g. 'Update 48' for Patch 48)")
    ap.add_argument("--limit", type=int, default=None, help="Max playerSkills records to scan (default: all)")
    args = ap.parse_args()

    print("Fetching playerSkills from ESO Log (class skills only)...")
    esolog_pairs = collect_class_lines_from_esolog(args.limit)
    print(f"  Found {len(esolog_pairs)} unique (classType, skillLine) from ESO Log")

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(args.db)
    row = conn.execute(
        "SELECT id FROM game_builds WHERE label = ?",
        (args.build_label,),
    ).fetchone()
    if not row:
        print(f"No game_build with label '{args.build_label}'", file=sys.stderr)
        conn.close()
        sys.exit(1)
    game_build_id = row[0]
    db_lines = load_db_class_lines(conn, game_build_id)
    conn.close()

    # Build expected set from DB: (class_name, line_name)
    db_pairs = {(cname, lname) for _cid, cname, _lid, lname in db_lines}
    # Normalize for comparison: ESO Log may use "Dawn's Wrath", we have "Dawn's Wrath" in seed
    esolog_normalized = set()
    for ct, sl in esolog_pairs:
        esolog_normalized.add((ct.strip(), sl.strip()))

    in_both = db_pairs & esolog_normalized
    only_esolog = esolog_normalized - db_pairs
    only_db = db_pairs - esolog_normalized

    print(f"\nDB class lines (this build): {len(db_pairs)}")
    print(f"ESO Log class lines (sampled): {len(esolog_normalized)}")
    print(f"Match (in both): {len(in_both)}")
    if only_esolog:
        print(f"Only in ESO Log (not in our seed): {len(only_esolog)}")
        for ct, sl in sorted(only_esolog):
            print(f"  - {ct!r} :: {sl!r}")
    if only_db:
        print(f"Only in DB (not seen in ESO Log sample): {len(only_db)}")
        for cname, lname in sorted(only_db):
            print(f"  - {cname!r} :: {lname!r}")

    if only_esolog and not only_db:
        print("\nConclusion: ESO Log has class lines we do not seed; consider adding or name mapping.")
    elif only_db and not only_esolog:
        print("\nConclusion: All ESO Log class lines match our seed; some DB lines not in sample (increase --limit).")
    elif not only_esolog and not only_db:
        print("\nConclusion: ESO Log class lines match our skill_lines seed (subclassing data consistent).")
    else:
        print("\nConclusion: Some name mismatches; check class/line names vs UESP/seed.")


if __name__ == "__main__":
    main()
