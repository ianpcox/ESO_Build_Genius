"""
Compute buff coverage for a build (slotted abilities + equipped set bonuses + optional passives).
Used to avoid recommending sets that only duplicate buffs already provided (e.g. Combat Prayer vs Kinras).

Usage:
  python scripts/buff_coverage.py [--db PATH] [--build-id N] [--abilities 1,2,3] [--sets "1,5" "2,5"]
  python scripts/buff_coverage.py --db data/eso_build_genius.db --build-id 1 --abilities 100,101 --sets "1,5"

If no args, prints coverage for build_id=1 with no abilities/sets (empty set).
"""
from __future__ import annotations

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_DB = os.path.join(ROOT_DIR, "data", "eso_build_genius.db")


def get_buff_coverage(
    conn,
    game_build_id: int,
    ability_ids: list[int] | None = None,
    set_pieces: list[tuple[int, int]] | None = None,
    skill_line_ids: list[int] | None = None,
) -> set[int]:
    """
    Return set of buff_ids already provided by the given abilities, set bonuses, and (optionally) passives.
    ability_ids: slotted ability ids.
    set_pieces: list of (set_id, num_pieces) for equipped sets.
    skill_line_ids: optional list of skill_line_ids for passives (e.g. from recommended_build_class_lines).
    """
    buff_ids: set[int] = set()
    if ability_ids:
        placeholders = ",".join("?" * len(ability_ids))
        cur = conn.execute(
            f"""
            SELECT DISTINCT buff_id FROM buff_grants
            WHERE game_build_id = ? AND grant_type = 'ability' AND ability_id IN ({placeholders})
            """,
            [game_build_id] + ability_ids,
        )
        buff_ids.update(row[0] for row in cur.fetchall())
    if set_pieces:
        for set_id, num_pieces in set_pieces:
            cur = conn.execute(
                """
                SELECT buff_id FROM buff_grants_set_bonus
                WHERE game_build_id = ? AND set_id = ? AND num_pieces = ?
                """,
                (game_build_id, set_id, num_pieces),
            )
            buff_ids.update(row[0] for row in cur.fetchall())
    if skill_line_ids:
        # Passives: any buff granted by a passive in one of these skill lines
        placeholders = ",".join("?" * len(skill_line_ids))
        cur = conn.execute(
            f"""
            SELECT DISTINCT buff_id FROM buff_grants
            WHERE game_build_id = ? AND grant_type = 'passive' AND skill_line_id IN ({placeholders})
            """,
            [game_build_id] + skill_line_ids,
        )
        buff_ids.update(row[0] for row in cur.fetchall())
    return buff_ids


def set_bonus_buff_ids(conn, game_build_id: int, set_id: int, num_pieces: int) -> set[int]:
    """Return buff_ids granted by this set bonus."""
    cur = conn.execute(
        """
        SELECT buff_id FROM buff_grants_set_bonus
        WHERE game_build_id = ? AND set_id = ? AND num_pieces = ?
        """,
        (game_build_id, set_id, num_pieces),
    )
    return {row[0] for row in cur.fetchall()}


def is_set_redundant_for_buffs(
    conn,
    game_build_id: int,
    coverage_buff_ids: set[int],
    set_id: int,
    num_pieces: int,
) -> bool:
    """
    True if this set bonus only grants buffs that are already in coverage (no new buffs).
    """
    bonus_buffs = set_bonus_buff_ids(conn, game_build_id, set_id, num_pieces)
    if not bonus_buffs:
        return False
    return bonus_buffs <= coverage_buff_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute buff coverage for a build")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--build-id", type=int, default=1, help="game_build_id")
    parser.add_argument("--abilities", type=str, default="", help="Comma-separated ability_ids")
    parser.add_argument("--sets", type=str, nargs="*", help='Pairs "set_id,num_pieces" e.g. "1,5"')
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    import sqlite3
    conn = sqlite3.connect(args.db)

    ability_ids = [int(x) for x in args.abilities.split(",") if x.strip()]
    set_pieces: list[tuple[int, int]] = []
    if args.sets:
        for s in args.sets:
            a, b = s.strip().split(",")
            set_pieces.append((int(a), int(b)))

    coverage = get_buff_coverage(conn, args.build_id, ability_ids=ability_ids or None, set_pieces=set_pieces or None)
    print(f"Buff coverage (build_id={args.build_id}): {sorted(coverage)}")

    # If Kinras (set_id=1, 5pc) is in the seed, show whether it would be redundant
    if 1 not in [s[0] for s in set_pieces]:
        redundant = is_set_redundant_for_buffs(conn, args.build_id, coverage, 1, 5)
        print(f"Kinras 5pc would add Minor Berserk (buff_id=1). Redundant for buffs? {redundant} (coverage has 1: {1 in coverage})")

    conn.close()


if __name__ == "__main__":
    main()
