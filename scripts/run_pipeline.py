#!/usr/bin/env python3
"""
Run the ESO Build Genius data pipeline in order: create_db, fetch, ingest sets/skills/food-potions, link skills.

Usage:
  python scripts/run_pipeline.py [--build-label "Update 48"] [--replace]
  python scripts/run_pipeline.py --skip-skills --skip-link-skills   # sets + buff grants + food/potions only
  python scripts/run_pipeline.py --dry-run                           # no DB writes (fetch only where applicable)

See docs/PIPELINE.md for full pipeline description and Makefile targets.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_DB = ROOT / "data" / "eso_build_genius.db"
DATA_DIR = ROOT / "data"


def run_step(cmd: list[str], desc: str, timeout: int | None = 300) -> bool:
    print("\n---", desc, "---")
    r = subprocess.run(
        cmd,
        cwd=str(ROOT),
        timeout=timeout,
        capture_output=False,
    )
    if r.returncode != 0:
        print("FAIL:", desc, "exit", r.returncode, file=sys.stderr)
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run ESO Build Genius data pipeline (create_db, fetch, ingest, link).",
        epilog="Steps run in order; use --skip-* to omit steps. See docs/PIPELINE.md.",
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-label", default="Update 48", help="Game build label for ingest steps")
    ap.add_argument("--replace", action="store_true", help="Pass --replace to ingest scripts where supported")
    ap.add_argument("--dry-run", action="store_true", help="Skip DB writes (fetch-only for fetches; ingests still need DB for --dry-run to affect them)")

    skips = ap.add_argument_group("Skip steps")
    skips.add_argument("--skip-db", action="store_true", help="Skip create_db")
    skips.add_argument("--skip-fetch", action="store_true", help="Skip fetch_foods_uesp and fetch_potions_uesp")
    skips.add_argument("--skip-sets", action="store_true", help="Skip ingest_sets_uesp")
    skips.add_argument("--skip-buff-grants", action="store_true", help="Skip populate_buff_grants_set_bonus")
    skips.add_argument("--skip-skills", action="store_true", help="Skip ingest_skills_uesp")
    skips.add_argument("--skip-link-skills", action="store_true", help="Skip link_skills_to_skill_lines")
    skips.add_argument("--skip-food-potions", action="store_true", help="Skip ingest_food_potions")

    optional = ap.add_argument_group("Optional steps (off by default)")
    optional.add_argument("--run-xlsx", action="store_true", dest="run_xlsx", help="Run ingest_xlsx (Damage Skills + stat ref + weapon comparisons)")
    optional.add_argument("--verify-esolog", action="store_true", help="Run verify_skill_lines_esolog after link_skills")
    optional.add_argument("--link-esolog", action="store_true", help="Run link_skill_lines_from_esolog after verify (if --verify-esolog) or link_skills")

    args = ap.parse_args()
    db_str = str(args.db)
    replace_args = ["--replace"] if args.replace else []
    dry_args = ["--dry-run"] if args.dry_run else []

    if not args.skip_db:
        if not run_step(["python", "scripts/create_db.py", db_str], "create_db", timeout=120):
            return 1

    if not args.skip_fetch:
        if not run_step(["python", "scripts/fetch_foods_uesp.py", "--out", str(DATA_DIR / "foods.json")], "fetch_foods_uesp", timeout=120):
            return 1
        if not run_step(["python", "scripts/fetch_potions_uesp.py", "--out", str(DATA_DIR / "potions.json")], "fetch_potions_uesp", timeout=60):
            return 1

    if not args.skip_sets:
        cmd = ["python", "scripts/ingest_sets_uesp.py", "--db", db_str, "--build-label", args.build_label] + replace_args + dry_args
        if not run_step(cmd, "ingest_sets_uesp", timeout=120):
            return 1

    if not args.skip_buff_grants:
        cmd = ["python", "scripts/populate_buff_grants_set_bonus.py", "--db", db_str, "--build-label", args.build_label] + replace_args + dry_args
        if not run_step(cmd, "populate_buff_grants_set_bonus", timeout=60):
            return 1

    if not args.skip_skills:
        cmd = ["python", "scripts/ingest_skills_uesp.py", "--db", db_str, "--build-label", args.build_label] + replace_args + dry_args
        if not run_step(cmd, "ingest_skills_uesp", timeout=600):
            return 1

    if not args.skip_link_skills:
        if not run_step(["python", "scripts/link_skills_to_skill_lines.py", "--db", db_str], "link_skills_to_skill_lines", timeout=60):
            return 1

    if not args.skip_food_potions and not args.dry_run:
        foods_json = DATA_DIR / "foods.json"
        potions_json = DATA_DIR / "potions.json"
        cmd = ["python", "scripts/ingest_food_potions.py", "--db", db_str, "--build-label", args.build_label]
        if foods_json.exists():
            cmd += ["--foods-json", str(foods_json)]
        if potions_json.exists():
            cmd += ["--potions-json", str(potions_json)]
        if not (foods_json.exists() or potions_json.exists()):
            print("\n--- ingest_food_potions (skipped: no foods.json or potions.json) ---")
        else:
            cmd += replace_args
            if not run_step(cmd, "ingest_food_potions", timeout=60):
                return 1

    if args.run_xlsx and not args.dry_run:
        cmd = ["python", "scripts/ingest_xlsx.py", "--db", db_str, "--build-label", args.build_label]
        if not run_step(cmd, "ingest_xlsx", timeout=90):
            return 1

    if args.verify_esolog:
        if not run_step(
            ["python", "scripts/verify_skill_lines_esolog.py", "--db", db_str, "--build-label", args.build_label],
            "verify_skill_lines_esolog",
            timeout=120,
        ):
            return 1

    if args.link_esolog and not args.dry_run:
        cmd = ["python", "scripts/link_skill_lines_from_esolog.py", "--db", db_str, "--build-label", args.build_label] + replace_args
        if not run_step(cmd, "link_skill_lines_from_esolog", timeout=300):
            return 1

    print("\n--- Pipeline finished ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
