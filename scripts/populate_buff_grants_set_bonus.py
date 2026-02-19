"""
Populate buff_grants_set_bonus from set_bonuses by parsing set_bonus_desc for known buff names.

Requires: set_summary and set_bonuses already ingested (e.g. ingest_sets_uesp.py), and buffs
catalog including extended buffs (schema 07 + 07b). Run after ingest_sets_uesp and after
create_db (or ensure 07b_seed_buffs_full.sql has been applied).

Usage:
  python scripts/populate_buff_grants_set_bonus.py --build-label "Update 48"
  python scripts/populate_buff_grants_set_bonus.py --build-id 1 --replace
  python scripts/populate_buff_grants_set_bonus.py --build-label "Update 48" --dry-run

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: set data from addon or UESP; this script derives set->buff from set_bonuses).
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DEFAULT_DB = DATA_DIR / "eso_build_genius.db"


def get_build_id(conn: sqlite3.Connection, *, build_id: int | None = None, build_label: str | None = None) -> int:
    if build_id is not None:
        r = conn.execute("SELECT id FROM game_builds WHERE id = ?", (build_id,)).fetchone()
        if not r:
            raise ValueError(f"No game_build with id={build_id}")
        return r[0]
    if build_label:
        r = conn.execute("SELECT id FROM game_builds WHERE label = ?", (build_label,)).fetchone()
        if not r:
            raise ValueError(f"No game_build with label={build_label!r}")
        return r[0]
    raise ValueError("Specify --build-id or --build-label")


def load_buff_names(conn: sqlite3.Connection, game_build_id: int) -> list[tuple[int, str]]:
    """Return (buff_id, name) for all buffs in this build, sorted by name length descending (longest first)."""
    rows = conn.execute(
        "SELECT buff_id, name FROM buffs WHERE game_build_id = ? ORDER BY LENGTH(name) DESC",
        (game_build_id,),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def extract_buff_ids_from_text(text: str, buff_names: list[tuple[int, str]]) -> set[int]:
    """Find all buff_ids whose name appears in text (case-insensitive)."""
    if not text or not text.strip():
        return set()
    lower = text.lower()
    found: set[int] = set()
    for buff_id, name in buff_names:
        if name.lower() in lower:
            found.add(buff_id)
    return found


def populate(
    conn: sqlite3.Connection,
    game_build_id: int,
    *,
    replace: bool = False,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    For each set_bonuses row, parse set_bonus_desc for buff names and insert into buff_grants_set_bonus.
    Returns (rows_considered, rows_inserted).
    """
    buff_names = load_buff_names(conn, game_build_id)
    if not buff_names:
        return 0, 0

    if replace and not dry_run:
        conn.execute("DELETE FROM buff_grants_set_bonus WHERE game_build_id = ?", (game_build_id,))

    rows = conn.execute(
        """
        SELECT game_id, num_pieces, set_bonus_desc
        FROM set_bonuses
        WHERE game_build_id = ?
        """,
        (game_build_id,),
    ).fetchall()

    inserted = 0
    for game_id, num_pieces, set_bonus_desc in rows:
        buff_ids = extract_buff_ids_from_text(set_bonus_desc or "", buff_names)
        for buff_id in buff_ids:
            if dry_run:
                inserted += 1
                continue
            try:
                before = conn.total_changes
                conn.execute(
                    """
                    INSERT OR IGNORE INTO buff_grants_set_bonus (game_build_id, buff_id, game_id, num_pieces)
                    VALUES (?, ?, ?, ?)
                    """,
                    (game_build_id, buff_id, game_id, num_pieces),
                )
                if conn.total_changes > before:
                    inserted += 1
            except sqlite3.IntegrityError:
                pass  # FK or duplicate

    if not dry_run:
        conn.commit()
    return len(rows), inserted


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Populate buff_grants_set_bonus by parsing set_bonus_desc for buff names"
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, default=None, help="Game build id")
    ap.add_argument("--build-label", type=str, default="Update 48", help="Game build label (use 'Update 48' for Patch 48)")
    ap.add_argument("--replace", action="store_true", help="Replace existing buff_grants_set_bonus for this build")
    ap.add_argument("--dry-run", action="store_true", help="Do not write; report count of matches")
    args = ap.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(args.db))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        game_build_id = get_build_id(conn, build_id=args.build_id, build_label=args.build_label)
        considered, inserted = populate(
            conn, game_build_id, replace=args.replace, dry_run=args.dry_run
        )
        if args.dry_run:
            print(f"Dry run: would insert up to {inserted} buff_grants_set_bonus rows from {considered} set bonus lines")
        else:
            print(f"Inserted {inserted} buff_grants_set_bonus rows from {considered} set bonus lines (build_id={game_build_id})")
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
