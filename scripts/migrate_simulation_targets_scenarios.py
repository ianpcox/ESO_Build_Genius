"""
One-off migration: add encounter_type and hp to simulation_targets
if the table was created before schema/03_xlsx_driven_schema.sql was updated.
Also backfills existing rows and inserts trial_trash_generic (id 3) if missing.

Usage: python scripts/migrate_simulation_targets_scenarios.py [--db PATH]
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
    cur = conn.execute("PRAGMA table_info(simulation_targets)")
    cols = {row[1] for row in cur.fetchall()}
    added = []
    if "encounter_type" not in cols:
        conn.execute(
            "ALTER TABLE simulation_targets ADD COLUMN encounter_type TEXT NOT NULL DEFAULT 'single_target'"
        )
        added.append("encounter_type")
    if "hp" not in cols:
        conn.execute("ALTER TABLE simulation_targets ADD COLUMN hp INTEGER")
        added.append("hp")

    if "hp" in added:
        conn.execute("UPDATE simulation_targets SET hp = 21000000 WHERE id = 2")

    cur = conn.execute("SELECT id FROM simulation_targets WHERE id = 3")
    if cur.fetchone() is None:
        conn.execute(
            """INSERT OR IGNORE INTO simulation_targets (id, name, resistance, encounter_type, hp, notes) VALUES
            (3, 'trial_trash_generic', 18200, 'aoe', NULL, 'Generic trial trash pack; AOE/cleave optimisation. Resistance same as boss; no HP (duration N/A). Per-trial trash can get dedicated scenarios later.')"""
        )
        added.append("trial_trash_generic row")

    conn.commit()
    conn.close()
    if added:
        print("Migration applied:", ", ".join(added))
    else:
        print("simulation_targets already has encounter_type, hp, and trial_trash_generic.")


if __name__ == "__main__":
    main()
