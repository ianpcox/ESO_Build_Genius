#!/usr/bin/env python3
"""
Set skills.skill_line_id from ESO Log playerSkills (classType + skillLine name).
Fetches playerSkills, maps skill line name to our skill_lines.skill_line_id,
then updates skills for matching ability_id. Helps subclassing and buff coverage
(skill_line_ids for passives). Run after ingest_skills_uesp if you want
skill_line_id populated from ESO Log instead of (or in addition to) xlsx link.

Usage:
  python scripts/link_skill_lines_from_esolog.py --build-label "Update 48"
  python scripts/link_skill_lines_from_esolog.py --build-id 1 --replace
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


def fetch_player_skills(limit: int, offset: int) -> list[dict]:
    url = f"{BASE_URL}?table=playerSkills&limit={limit}&offset={offset}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data.get("playerSkills") or []


def load_name_to_line_id(conn: sqlite3.Connection, game_build_id: int) -> dict[str, int]:
    """Map skill_lines.name -> skill_line_id for this build."""
    rows = conn.execute(
        "SELECT name, skill_line_id FROM skill_lines WHERE game_build_id = ?",
        (game_build_id,),
    ).fetchall()
    return {name.strip(): sid for name, sid in rows}


def main() -> None:
    ap = argparse.ArgumentParser(description="Link skills.skill_line_id from ESO Log playerSkills")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, help="Game build id")
    ap.add_argument("--build-label", default="Update 48", help="Game build label (e.g. 'Update 48' for Patch 48; if no --build-id)")
    ap.add_argument("--limit", type=int, default=None, help="Max playerSkills to fetch (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(args.db)
    if args.build_id:
        r = conn.execute("SELECT id FROM game_builds WHERE id = ?", (args.build_id,)).fetchone()
        if not r:
            print(f"No game_build id={args.build_id}", file=sys.stderr)
            conn.close()
            sys.exit(1)
        game_build_id = args.build_id
    else:
        r = conn.execute(
            "SELECT id FROM game_builds WHERE label = ?",
            (args.build_label,),
        ).fetchone()
        if not r:
            print(f"No game_build label={args.build_label!r}", file=sys.stderr)
            conn.close()
            sys.exit(1)
        game_build_id = r[0]

    name_to_id = load_name_to_line_id(conn, game_build_id)
    print(f"Loaded {len(name_to_id)} skill line names for game_build_id={game_build_id}")

    updates: list[tuple[int, int]] = []  # (ability_id, skill_line_id)
    offset = 0
    # Pagination cap when no --limit. playerSkills is a subset of minedSkills (isPlayer=1); 999999 = fetch all.
    max_records = args.limit or 999999
    while len(updates) < max_records:
        chunk = fetch_player_skills(min(CHUNK, max_records - len(updates)), offset)
        if not chunk:
            break
        for rec in chunk:
            sl_name = (rec.get("skillLine") or "").strip()
            if not sl_name:
                continue
            line_id = name_to_id.get(sl_name)
            if line_id is None:
                continue
            try:
                aid = int(rec.get("id") or rec.get("displayId") or 0)
            except (TypeError, ValueError):
                continue
            if aid <= 0:
                continue
            updates.append((aid, line_id))
        if len(chunk) < CHUNK:
            break
        offset += len(chunk)
        time.sleep(0.3)

    # Dedupe by ability_id (last wins)
    by_ability: dict[int, int] = {}
    for aid, line_id in updates:
        by_ability[aid] = line_id

    print(f"Resolved {len(by_ability)} ability_ids to skill_line_id from ESO Log")

    if args.dry_run:
        sample = list(by_ability.items())[:5]
        print(f"Dry run: would update {len(by_ability)} skills. Sample: {sample}")
        conn.close()
        return

    updated = 0
    for ability_id, skill_line_id in by_ability.items():
        cur = conn.execute(
            "UPDATE skills SET skill_line_id = ? WHERE game_build_id = ? AND ability_id = ?",
            (skill_line_id, game_build_id, ability_id),
        )
        updated += cur.rowcount
    conn.commit()
    conn.close()
    print(f"Updated skills.skill_line_id for {updated} rows.")


if __name__ == "__main__":
    main()
