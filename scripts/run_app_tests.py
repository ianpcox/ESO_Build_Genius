#!/usr/bin/env python3
"""
Smoke tests for ESO Build Genius: create_db, demos, optimizer, subclassing, recommendations.

Usage:
  python scripts/run_app_tests.py [--db PATH]
  python scripts/run_app_tests.py --no-create   # use existing DB

Expects: data/eso_build_genius.db (created if missing, unless --no-create).
Optional: run ingest_sets_uesp / ingest_skills_uesp for more sets and skills.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_DB = ROOT / "data" / "eso_build_genius.db"


def run(cmd: list[str], desc: str, timeout: int = 60) -> bool:
    print("\n---", desc, "---")
    r = subprocess.run(
        cmd,
        cwd=str(ROOT),
        timeout=timeout,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        print("FAIL:", desc, "exit", r.returncode)
        return False
    print(r.stdout or "(ok)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Run application smoke tests")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--no-create", action="store_true", help="Skip create_db (use existing DB)")
    args = ap.parse_args()

    if not args.no_create:
        if not run(["python", "scripts/create_db.py", str(args.db)], "create_db", timeout=90):
            return 1

    tests = [
        (["python", "scripts/stat_block_damage_demo.py", "--db", str(args.db), "--build-id", "1"], "stat_block_damage_demo"),
        (["python", "scripts/weapon_comparison_demo.py", "--db", str(args.db)], "weapon_comparison_demo"),
        (["python", "scripts/run_optimizer.py", "--db", str(args.db), "--build-id", "1", "--limit", "15", "--top", "2", "--dry-run"], "run_optimizer (dry-run)"),
        (["python", "scripts/run_optimizer.py", "--db", str(args.db), "--build-id", "1", "--limit", "10", "--top", "2"], "run_optimizer (write 2 builds)"),
        (["python", "scripts/recommend_sets.py", "--db", str(args.db), "--build-id", "1", "--slot", "1", "--limit", "2"], "recommend_sets"),
        (["python", "scripts/buff_coverage.py", "--db", str(args.db), "--build-id", "1"], "buff_coverage"),
    ]
    for cmd, desc in tests:
        if not run(cmd, desc):
            return 1

    # Subclassing validation on saved builds
    code = """
from core.subclassing import validate_subclass_lines
import sqlite3
conn = sqlite3.connect(r'%s')
rows = conn.execute("SELECT id FROM recommended_builds ORDER BY id DESC LIMIT 2").fetchall()
for (bid,) in rows:
    assert validate_subclass_lines(conn, bid), "build %%s" %% bid
conn.close()
""" % str(args.db.resolve())
    if not run([sys.executable, "-c", code], "subclassing validation"):
        return 1

    print("\n--- All tests passed ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
