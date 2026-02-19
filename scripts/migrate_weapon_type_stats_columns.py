"""
One-off migration: add bonus_penetration and bonus_crit_rating to weapon_type_stats
if the table was created before schema/03_xlsx_driven_schema.sql was updated.

Usage: python scripts/migrate_weapon_type_stats_columns.py [--db PATH]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DEFAULT_DB = ROOT_DIR / "data" / "eso_build_genius.db"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()
    if not args.db.exists():
        print("DB not found:", args.db, file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(str(args.db))
    cur = conn.execute("PRAGMA table_info(weapon_type_stats)")
    cols = {row[1] for row in cur.fetchall()}
    added = []
    if "bonus_penetration" not in cols:
        conn.execute("ALTER TABLE weapon_type_stats ADD COLUMN bonus_penetration REAL")
        added.append("bonus_penetration")
    if "bonus_crit_rating" not in cols:
        conn.execute("ALTER TABLE weapon_type_stats ADD COLUMN bonus_crit_rating REAL")
        added.append("bonus_crit_rating")
    conn.commit()
    conn.close()
    if added:
        print("Added columns:", ", ".join(added))
    else:
        print("Table already has bonus_penetration and bonus_crit_rating.")


if __name__ == "__main__":
    main()
