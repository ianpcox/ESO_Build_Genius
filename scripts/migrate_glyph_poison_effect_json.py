#!/usr/bin/env python3
"""
One-time migration: add effect_json to glyphs and weapon_poisons if missing, then seed values.
Run if your DB was created before effect_json was added to the schema.

Usage: python scripts/migrate_glyph_poison_effect_json.py [--db PATH]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_DB = ROOT / "data" / "eso_build_genius.db"


def has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM pragma_table_info(?) WHERE name = ?",
        (table, column),
    ).fetchone()
    return row is not None


def main() -> int:
    ap = argparse.ArgumentParser(description="Add effect_json to glyphs/weapon_poisons and seed")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    args = ap.parse_args()

    if not args.db.is_file():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(args.db))
    conn.execute("PRAGMA foreign_keys = ON")

    for table, column in [("glyphs", "effect_json"), ("weapon_poisons", "effect_json")]:
        if not has_column(conn, table, column):
            print(f"Adding {column} to {table} ...")
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
        else:
            print(f"{table}.{column} already exists, skipping ALTER")

    updates = [
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 1", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"fire"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 2", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"shock"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 3", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"frost"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 4", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"poison"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 5", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"disease"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 6", '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"oblivion"}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 7", '{"type":"buff","stat":"weapon_spell_damage","amount":258,"duration_sec":5,"cooldown_sec":5}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 8", '{"type":"absorb","damage":400,"heal":400,"cooldown_sec":4}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 9", '{"type":"absorb","damage":400,"resource":"magicka","amount":400,"cooldown_sec":4}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 10", '{"type":"absorb","damage":400,"resource":"stamina","amount":400,"cooldown_sec":4}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 11", '{"type":"debuff","stat":"resistance","amount":2108,"duration_sec":5,"cooldown_sec":5}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 12", '{"type":"debuff","stat":"weapon_spell_damage","amount":-258,"duration_sec":5,"cooldown_sec":5}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 13", '{"type":"shield","amount":5000,"duration_sec":5,"cooldown_sec":5}'),
        ("glyphs", "effect_json", "slot_kind = 'weapon' AND glyph_id = 14", '{"type":"prismatic","damage":300,"heal":300,"magicka":300,"stamina":300,"cooldown_sec":4}'),
        ("weapon_poisons", "effect_json", "poison_id = 1", '{"type":"dot","damage":1200,"duration_sec":4,"healing_received_debuff":true}'),
        ("weapon_poisons", "effect_json", "poison_id = 2", '{"type":"dot","damage":1400,"duration_sec":4}'),
        ("weapon_poisons", "effect_json", "poison_id = 3", '{"type":"debuff","damage_taken_pct":0.10,"duration_sec":4}'),
    ]
    for table, col, where, val in updates:
        conn.execute(f"UPDATE {table} SET {col} = ? WHERE {where}", (val,))
    conn.commit()
    conn.close()
    print("Migration done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
