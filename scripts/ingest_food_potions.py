"""
Ingest foods and/or potions from local JSON into the ESO Build Genius DB.

Use when you have exported data (e.g. from addon, manual list, or scraped wiki).
Seed data for mundus + minimal food/potion lives in schema/10_seed_mundus_food_potions.sql;
this script adds or replaces rows from JSON for a given game build.

Expected JSON format:
  foods:    [ { "food_id": 1, "name": "...", "duration_sec": 7200, "effect_text": "...", "effect_json": null }, ... ]
  potions:  [ { "potion_id": 1, "name": "...", "duration_sec": 47.5, "cooldown_sec": 45, "effect_text": "...", "effect_json": null }, ... ]

Usage:
  python scripts/ingest_food_potions.py --build-label "Update 48" --foods-json data/foods.json
  python scripts/ingest_food_potions.py --build-id 1 --potions-json data/potions.json
  python scripts/ingest_food_potions.py --build-label "Update 48" --foods-json data/foods.json --potions-json data/potions.json --replace

If neither --foods-json nor --potions-json is given, prints usage and notes the seed file.

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: prefer addon export for food/potion catalogs when available).
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


def get_build_id(conn: sqlite3.Connection, *, build_id: int | None = None, build_label: str | None = None) -> int:
    if build_id is not None:
        r = conn.execute("SELECT id FROM game_builds WHERE id = ?", (build_id,)).fetchone()
        if not r:
            raise SystemExit(f"No game_build with id={build_id}")
        return r[0]
    if build_label:
        r = conn.execute("SELECT id FROM game_builds WHERE label = ?", (build_label,)).fetchone()
        if not r:
            raise SystemExit(f"No game_build with label={build_label!r}")
        return r[0]
    raise SystemExit("Specify --build-id or --build-label")


def ingest_foods(
    conn: sqlite3.Connection,
    game_build_id: int,
    items: list[dict],
    *,
    replace: bool = False,
) -> int:
    if replace:
        conn.execute("DELETE FROM foods WHERE game_build_id = ?", (game_build_id,))
    count = 0
    for o in items:
        food_id = int(o["food_id"])
        name = o.get("name") or ""
        duration_sec = o.get("duration_sec")
        effect_text = o.get("effect_text") or ""
        effect_json = o.get("effect_json")
        if effect_json is not None and not isinstance(effect_json, str):
            effect_json = json.dumps(effect_json)
        conn.execute(
            """INSERT OR REPLACE INTO foods (game_build_id, food_id, name, duration_sec, effect_text, effect_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (game_build_id, food_id, name, duration_sec, effect_text, effect_json),
        )
        count += 1
    return count


def ingest_potions(
    conn: sqlite3.Connection,
    game_build_id: int,
    items: list[dict],
    *,
    replace: bool = False,
) -> int:
    if replace:
        conn.execute("DELETE FROM potions WHERE game_build_id = ?", (game_build_id,))
    count = 0
    for o in items:
        potion_id = int(o["potion_id"])
        name = o.get("name") or ""
        duration_sec = o.get("duration_sec")
        cooldown_sec = o.get("cooldown_sec")
        effect_text = o.get("effect_text") or ""
        effect_json = o.get("effect_json")
        if effect_json is not None and not isinstance(effect_json, str):
            effect_json = json.dumps(effect_json)
        conn.execute(
            """INSERT OR REPLACE INTO potions (game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_text, effect_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_text, effect_json),
        )
        count += 1
    return count


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest foods and/or potions from JSON into the DB.")
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite DB")
    ap.add_argument("--build-id", type=int, help="Game build id")
    ap.add_argument("--build-label", help="Game build label (e.g. 'Update 48' for Patch 48)")
    ap.add_argument("--foods-json", help="Path to JSON array of food objects")
    ap.add_argument("--potions-json", help="Path to JSON array of potion objects")
    ap.add_argument("--replace", action="store_true", help="Replace existing foods/potions for this build before inserting")
    ap.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    args = ap.parse_args()

    if not args.foods_json and not args.potions_json:
        print("No --foods-json or --potions-json given.")
        print("Seed data (mundus + minimal food/potion) is in schema/10_seed_mundus_food_potions.sql")
        print("To add more: provide JSON files from addon export or see docs/DATA_SOURCES.md.")
        return

    if not args.build_id and not args.build_label:
        raise SystemExit("Specify --build-id or --build-label")

    conn = sqlite3.connect(args.db)
    game_build_id = get_build_id(conn, build_id=args.build_id, build_label=args.build_label)
    if args.dry_run:
        total = 0
        if args.foods_json:
            path = os.path.join(ROOT_DIR, args.foods_json) if not os.path.isabs(args.foods_json) else args.foods_json
            with open(path, encoding="utf-8") as f:
                foods = json.load(f)
            total += len(foods)
            print(f"Foods: would insert {len(foods)} rows")
        if args.potions_json:
            path = os.path.join(ROOT_DIR, args.potions_json) if not os.path.isabs(args.potions_json) else args.potions_json
            with open(path, encoding="utf-8") as f:
                potions = json.load(f)
            total += len(potions)
            print(f"Potions: would insert {len(potions)} rows")
        print(f"Dry run: total {total} rows for game_build_id={game_build_id}")
        conn.close()
        return

    total = 0
    if args.foods_json:
        path = os.path.join(ROOT_DIR, args.foods_json) if not os.path.isabs(args.foods_json) else args.foods_json
        with open(path, encoding="utf-8") as f:
            foods = json.load(f)
        n = ingest_foods(conn, game_build_id, foods, replace=args.replace)
        total += n
        print(f"Foods: {n} rows")
    if args.potions_json:
        path = os.path.join(ROOT_DIR, args.potions_json) if not os.path.isabs(args.potions_json) else args.potions_json
        with open(path, encoding="utf-8") as f:
            potions = json.load(f)
        n = ingest_potions(conn, game_build_id, potions, replace=args.replace)
        total += n
        print(f"Potions: {n} rows")

    conn.commit()
    conn.close()
    print(f"Total: {total} rows for game_build_id={game_build_id}")


if __name__ == "__main__":
    main()
