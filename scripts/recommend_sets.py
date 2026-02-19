"""
Recommend sets for a slot using self-buff coverage. Avoids sets that only duplicate
buffs already provided by abilities, passives, and other equipped sets.

Usage:
  python scripts/recommend_sets.py --slot 1
  python scripts/recommend_sets.py --db data/eso_build_genius.db --build-id 1 --slot 5 --abilities 100,101 --sets "1,5" "2,5"
  python scripts/recommend_sets.py --slot 1 --equipment "1,846" "2,806" --show-buffs

--sets: current equipment as "game_id,num_pieces" (used for coverage; does not include slot assignment).
--equipment: current equipment as "slot_id,game_id" pairs (game_id = UESP setSummary gameId).
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_DB = os.path.join(ROOT_DIR, "data", "eso_build_genius.db")

# Import after path fix
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from recommendations import (
    get_buff_names,
    get_self_buff_coverage,
    get_set_recommendations_for_slot,
)


def _parse_equipment(args_equipment: list[str]) -> list[tuple[int, int]]:
    """Parse --equipment "slot_id,set_id" ... into [(slot_id, set_id), ...]."""
    out: list[tuple[int, int]] = []
    for s in args_equipment or []:
        a, b = s.strip().split(",")
        out.append((int(a), int(b)))
    return out


def _parse_set_pieces(args_sets: list[str]) -> list[tuple[int, int]]:
    """Parse --sets "set_id,num_pieces" ... into [(set_id, num_pieces), ...]. Then build equipment from slot list."""
    return [(int(a), int(b)) for s in (args_sets or []) for a, b in [s.strip().split(",")]]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Recommend sets for a slot using self-buff coverage (self-buffs only)."
    )
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, default=1, help="game_build_id (use the build that has set_summary/set_item_slots, e.g. 2 if you ingested UESP into Default)")
    ap.add_argument("--slot", type=int, required=True, help="equipment_slots.id to recommend for (e.g. 1=head)")
    ap.add_argument("--abilities", type=str, default="", help="Comma-separated ability_ids (slotted)")
    ap.add_argument(
        "--equipment",
        type=str,
        nargs="*",
        help='Current equipment: "slot_id,game_id" per slot (e.g. "1,846" "2,806")',
    )
    ap.add_argument(
        "--sets",
        type=str,
        nargs="*",
        help='Legacy: "game_id,num_pieces" for coverage (e.g. "846,5"); use --equipment for slot-aware.',
    )
    ap.add_argument("--skill-lines", type=str, default="", help="Comma-separated skill_line_ids for passives")
    ap.add_argument("--show-buffs", action="store_true", help="Print current self-buff coverage (names)")
    ap.add_argument("--limit", type=int, default=0, help="Max recommendations to print (0 = all)")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    ability_ids = [int(x) for x in args.abilities.split(",") if x.strip()]
    skill_line_ids = [int(x) for x in args.skill_lines.split(",") if x.strip()]
    equipment = _parse_equipment(args.equipment) if args.equipment else []
    if not equipment and args.sets:
        set_pieces = _parse_set_pieces(args.sets)
        equipment = []
        slot = 1
        for game_id, num_pieces in set_pieces:
            for _ in range(num_pieces):
                if slot <= 14:
                    equipment.append((slot, game_id))
                    slot += 1
            if slot > 14:
                break

    conn = sqlite3.connect(args.db)
    try:
        recs = get_set_recommendations_for_slot(
            conn,
            args.build_id,
            args.slot,
            ability_ids=ability_ids or None,
            equipment=equipment or None,
            skill_line_ids=skill_line_ids or None,
        )
        from collections import Counter
        set_pieces = list(Counter(gid for _, gid in equipment).items()) if equipment else None
        coverage = get_self_buff_coverage(
            conn,
            args.build_id,
            ability_ids=ability_ids or None,
            set_pieces=set_pieces,
            skill_line_ids=skill_line_ids or None,
        )
        coverage_list = sorted(coverage)
        if args.show_buffs:
            names = get_buff_names(conn, args.build_id, coverage_list)
            print(f"Self-buff coverage ({len(coverage_list)}): {[names.get(b, str(b)) for b in coverage_list]}")
            print()
        else:
            print(f"Self-buff coverage: {len(coverage_list)} buffs (use --show-buffs for names)")
            print()

        to_show = recs[: args.limit] if args.limit else recs
        print(f"Slot {args.slot}: {len(recs)} candidate sets (showing {len(to_show)})")
        print("-" * 60)
        for r in to_show:
            red = " [REDUNDANT for self-buffs]" if r["is_fully_redundant"] else ""
            print(f"  {r['set_name']} (game_id={r['game_id']}, {r['type']}, max {r['set_max_equip_count']}pc){red}")
            if r["redundant_bonuses"]:
                print(f"    Redundant bonuses: {r['redundant_bonuses']}pc")
            if r["adding_bonuses"]:
                print(f"    Adding bonuses: {r['adding_bonuses']}pc")
        if args.limit and len(recs) > args.limit:
            print(f"  ... and {len(recs) - args.limit} more")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
