#!/usr/bin/env python3
"""
Create or reset the ESO Build Genius SQLite database from schema files.
Usage: python scripts/create_db.py [path_to_db]
Default DB path: data/eso_build_genius.db
"""

import sqlite3
import sys
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schema"
DEFAULT_DB = PROJECT_ROOT / "data" / "eso_build_genius.db"


def main() -> None:
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_files = sorted(SCHEMA_DIR.glob("*.sql"))
    if not schema_files:
        print("No .sql files found in schema/")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")

    for path in schema_files:
        print(f"Running {path.name} ...")
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)

    conn.commit()
    conn.close()
    print(f"Database created: {db_path}")


if __name__ == "__main__":
    main()
