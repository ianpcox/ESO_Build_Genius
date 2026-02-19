"""
Ingest the scribing script catalog into scribe_effects from data/scribe_effects.json.

Expects JSON produced by fetch_scribe_effects_uesp.py with keys: focus, signature, affix
(each a list of { "name": "..." }). Assigns stable scribe_effect_id: Focus 1..21,
Signature 22..41, Affix 42..67. Replaces all existing scribe_effects for each game build.

Usage:
  python scripts/ingest_scribe_effects.py
  python scripts/ingest_scribe_effects.py --db data/eso_build_genius.db --replace
  python scripts/ingest_scribe_effects.py --dry-run

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: prefer addon/game source for catalog when available; UESP for validation).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "eso_build_genius.db")
DEFAULT_JSON = os.path.join(DATA_DIR, "scribe_effects.json")

# Stable ID ranges: Focus 1-21, Signature 22-41, Affix 42-67
FOCUS_ID_START = 1
SIGNATURE_ID_START = 22
AFFIX_ID_START = 42


def load_catalog(path: str) -> tuple[list[dict], list[dict], list[dict]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    focus = data.get("focus") or []
    signature = data.get("signature") or []
    affix = data.get("affix") or []
    return focus, signature, affix


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest scribe effects from JSON into DB")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite database path")
    ap.add_argument("--json", default=DEFAULT_JSON, help="Input scribe_effects.json path")
    ap.add_argument("--replace", action="store_true", help="Replace existing scribe_effects per build (default: True)")
    ap.add_argument("--dry-run", action="store_true", help="Print planned inserts only")
    args = ap.parse_args()

    if not os.path.isfile(args.json):
        raise SystemExit(f"Input file not found: {args.json}")

    focus, signature, affix = load_catalog(args.json)
    # (scribe_effect_id, name, slot_id) template; game_build_id filled per build
    rows: list[tuple[int, str, int]] = []
    for i, item in enumerate(focus):
        rows.append((FOCUS_ID_START + i, item["name"], 1))
    for i, item in enumerate(signature):
        rows.append((SIGNATURE_ID_START + i, item["name"], 2))
    for i, item in enumerate(affix):
        rows.append((AFFIX_ID_START + i, item["name"], 3))

    if args.dry_run:
        print(f"Would insert {len(rows)} scribe effects per game build (Focus {len(focus)}, Signature {len(signature)}, Affix {len(affix)})")
        for eid, name, slot in rows[:10]:
            print(f"  scribe_effect_id={eid}, name={name!r}, slot_id={slot}")
        print("  ...")
        return

    if not os.path.isfile(args.db):
        raise SystemExit(f"Database not found: {args.db}")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id FROM game_builds ORDER BY id")
    build_ids = [r["id"] for r in cur.fetchall()]
    if not build_ids:
        print("No game_builds in DB; nothing to do.")
        conn.close()
        return

    for gid in build_ids:
        cur.execute("DELETE FROM scribe_effects WHERE game_build_id = ?", (gid,))
        for eid, name, slot_id in rows:
            cur.execute(
                """INSERT INTO scribe_effects (game_build_id, scribe_effect_id, name, slot_id, effect_text, effect_type, magnitude, resource_type)
                   VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL)""",
                (gid, eid, name, slot_id),
            )
    conn.commit()
    conn.close()
    print(f"Ingested {len(rows)} scribe effects for {len(build_ids)} game build(s).")


if __name__ == "__main__":
    main()
