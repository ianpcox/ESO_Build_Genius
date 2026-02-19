"""
First optimizer: enumerate valid 5+5+2 set combinations, score by stat proxy or real
damage-per-hit (when --ability-id is set), write top builds to recommended_builds and recommended_build_equipment.

Usage:
  python scripts/run_optimizer.py [--db PATH] [--build-id N] [--limit 50] [--top 10]
  python scripts/run_optimizer.py --ability-id 84700 --target-resistance 18200 --limit 30 --top 5
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from core.damage import damage_per_hit
from core.rotation import rotation_dps
from core.slot_rules import (
    enumerate_valid_combos,
    enumerate_valid_combos_mythic,
    expand_equipment_to_physical_slots,
)
from core.stat_block import compute_stat_block
from core.subclassing import ensure_build_class_lines

DEFAULT_DB = ROOT_DIR / "data" / "eso_build_genius.db"


def _score_stat_block(block) -> float:
    """Simple DPS proxy: sum of power and scaled penetration."""
    return block.weapon_damage + block.spell_damage + block.penetration / 100.0 + block.critical_rating / 100.0


def _score_damage_per_hit(
    conn: sqlite3.Connection,
    game_build_id: int,
    ability_id: int,
    block,
    use_stamina: bool,
    target_resistance: float,
    target_damage_taken_pct: float,
) -> float:
    """Score = damage_per_hit for one ability."""
    row = conn.execute(
        "SELECT coefficient_json, mechanic FROM skills WHERE game_build_id = ? AND ability_id = ?",
        (game_build_id, ability_id),
    ).fetchone()
    if not row or not row[0]:
        return 0.0
    use_stam = use_stamina or (row[1] == "Stamina")
    return damage_per_hit(
        block,
        row[0],
        use_stam,
        target_resistance=target_resistance,
        target_damage_taken_pct=target_damage_taken_pct,
    )


def _score_damage_rotation(
    conn: sqlite3.Connection,
    game_build_id: int,
    ability_ids: list[int],
    block,
    use_stamina: bool,
    target_resistance: float,
    target_damage_taken_pct: float,
    weights: list[float] | None = None,
) -> float:
    """Rotation-aware DPS = sum of (weight_i * damage_per_hit(ability_i)). Uses core.rotation.rotation_dps."""
    w = weights if weights else [1.0] * len(ability_ids)
    if len(w) < len(ability_ids):
        w = w + [1.0] * (len(ability_ids) - len(w))
    ability_weights = list(zip(ability_ids, w))
    return rotation_dps(
        conn,
        game_build_id,
        block,
        ability_weights,
        use_stamina=use_stamina,
        target_resistance=target_resistance,
        target_damage_taken_pct=target_damage_taken_pct,
    )


def _equipment_to_set_pieces(physical_assignment: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Convert [(slot_id, game_id), ...] to [(game_id, num_pieces), ...] for compute_stat_block."""
    from collections import Counter
    counts: dict[int, int] = Counter()
    for _slot_id, game_id in physical_assignment:
        counts[game_id] += 1
    return [(gid, count) for gid, count in counts.items()]


def main() -> None:
    ap = argparse.ArgumentParser(description="First optimizer: 5+5+2 set combos, score by stats, write top builds")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, default=1, help="game_build_id")
    ap.add_argument("--limit", type=int, default=100, help="Max set combinations to try (0 = no limit)")
    ap.add_argument("--top", type=int, default=10, help="Number of top builds to save")
    ap.add_argument("--race-id", type=int, default=1, help="race_id for stat block")
    ap.add_argument("--mundus-id", type=int, default=13, help="mundus_id (13=Warrior)")
    ap.add_argument("--food-id", type=int, default=1, help="food_id")
    ap.add_argument("--potion-id", type=int, default=1, help="potion_id")
    ap.add_argument("--class-id", type=int, default=1, help="class_id for recommended_builds")
    ap.add_argument("--role-id", type=int, default=1, help="role_id (1=dd)")
    ap.add_argument("--ability-id", type=int, default=None, help="Single ability for damage_per_hit scoring (legacy)")
    ap.add_argument("--ability-ids", type=str, default="", help="Comma-separated ability_ids for scoring; overrides --ability-id if set")
    ap.add_argument("--rotation-weights", type=str, default="", help="Comma-separated hits/sec per ability (same order as --ability-ids); e.g. 1.0,0.3 = spammable + DoT; default 1.0 each")
    ap.add_argument("--stamina", action="store_true", help="Use stamina for scoring abilities; else use skill mechanic")
    ap.add_argument("--target-resistance", type=float, default=18200.0, help="Target armor for mitigation (used with --ability-id)")
    ap.add_argument("--vuln-pct", type=float, default=0.10, help="Target damage-taken e.g. 0.10 for Major Vuln (with --ability-id)")
    ap.add_argument("--mythic", action="store_true", help="Use 5+4+2+1 (one mythic) instead of 5+5+2")
    ap.add_argument("--filter-redundant", action="store_true", help="Skip combos where one 5pc set only duplicates buffs from the rest")
    ap.add_argument("--abilities", type=str, default="", help="Comma-separated ability_ids for redundancy check (with --filter-redundant)")
    ap.add_argument("--skill-lines", type=str, default="", help="Comma-separated skill_line_ids for redundancy check")
    ap.add_argument("--dry-run", action="store_true", help="Do not insert into DB")
    args = ap.parse_args()

    if not args.db.exists():
        print("DB not found:", args.db, file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(args.db))
    conn.row_factory = sqlite3.Row

    ability_ids = [int(x) for x in args.abilities.split(",") if x.strip()] if args.abilities else None
    skill_line_ids = [int(x) for x in args.skill_lines.split(",") if x.strip()] if args.skill_lines else None
    if args.filter_redundant:
        from recommendations import is_combo_skipped_for_redundancy, is_combo_mythic_skipped_for_redundancy
        print("Filtering redundant combos (abilities=%s, skill_lines=%s)" % (ability_ids, skill_line_ids))

    scoring_ability_ids: list[int] = []
    if args.ability_ids.strip():
        scoring_ability_ids = [int(x) for x in args.ability_ids.split(",") if x.strip()]
    elif args.ability_id is not None:
        scoring_ability_ids = [args.ability_id]
    rotation_weights: list[float] | None = None
    if args.rotation_weights.strip():
        rotation_weights = [float(x) for x in args.rotation_weights.split(",") if x.strip()]
    use_dph = len(scoring_ability_ids) > 0
    if use_dph:
        names = []
        for aid in scoring_ability_ids:
            row = conn.execute(
                "SELECT name FROM skills WHERE game_build_id = ? AND ability_id = ?",
                (args.build_id, aid),
            ).fetchone()
            if not row:
                print("Ability id %s not found for build %s" % (aid, args.build_id), file=sys.stderr)
                sys.exit(1)
            names.append(row[0])
        wstr = (" weights=%s" % rotation_weights) if rotation_weights else ""
        print("Scoring by rotation DPS: ability_ids=%s (%s), target_res=%s%s" % (scoring_ability_ids, ", ".join(names), args.target_resistance, wstr))

    limit = args.limit if args.limit > 0 else 5000
    scored: list[tuple[float, list[tuple[int, int]], int, int, int, int | None]] = []
    count = 0
    if args.mythic:
        it = enumerate_valid_combos_mythic(
            conn, args.build_id,
            five_piece_limit=80,
            monster_limit=40,
            mythic_limit=20,
        )
        for set_a_id, set_b_id, monster_id, mythic_id, assignment in it:
            if args.filter_redundant and is_combo_mythic_skipped_for_redundancy(
                conn, args.build_id, set_a_id, set_b_id, monster_id, mythic_id,
                ability_ids=ability_ids,
                skill_line_ids=skill_line_ids,
            ):
                continue
            if count >= limit:
                break
            count += 1
            physical = expand_equipment_to_physical_slots(assignment)
            set_pieces = _equipment_to_set_pieces(physical)
            block = compute_stat_block(
                conn, args.build_id, args.race_id,
                set_pieces=set_pieces, food_id=args.food_id, potion_id=args.potion_id, mundus_id=args.mundus_id,
            )
            if use_dph:
                score = _score_damage_rotation(
                    conn, args.build_id, scoring_ability_ids, block,
                    args.stamina, args.target_resistance, args.vuln_pct,
                    weights=rotation_weights,
                )
            else:
                score = _score_stat_block(block)
            scored.append((score, physical, set_a_id, set_b_id, monster_id, mythic_id))
    else:
        for set_a_id, set_b_id, monster_id, assignment in enumerate_valid_combos(
            conn, args.build_id, five_piece_limit=80, monster_limit=40,
        ):
            if args.filter_redundant and is_combo_skipped_for_redundancy(
                conn, args.build_id, set_a_id, set_b_id, monster_id,
                ability_ids=ability_ids,
                skill_line_ids=skill_line_ids,
            ):
                continue
            if count >= limit:
                break
            count += 1
            physical = expand_equipment_to_physical_slots(assignment)
            set_pieces = _equipment_to_set_pieces(physical)
            block = compute_stat_block(
                conn, args.build_id, args.race_id,
                set_pieces=set_pieces, food_id=args.food_id, potion_id=args.potion_id, mundus_id=args.mundus_id,
            )
            if use_dph:
                score = _score_damage_rotation(
                    conn, args.build_id, scoring_ability_ids, block,
                    args.stamina, args.target_resistance, args.vuln_pct,
                    weights=rotation_weights,
                )
            else:
                score = _score_stat_block(block)
            scored.append((score, physical, set_a_id, set_b_id, monster_id, None))

    scored.sort(key=lambda x: -x[0])
    top = scored[: args.top]
    print("Tried %s combinations, saving top %s" % (count, len(top)))
    for i, (score, physical, a, b, m, my_id) in enumerate(top, 1):
        extra = " mythic=%s" % my_id if my_id is not None else ""
        print("  %s. score=%.1f sets A=%s B=%s monster=%s%s" % (i, score, a, b, m, extra))

    if args.dry_run or not top:
        conn.close()
        return

    for score, physical, set_a_id, set_b_id, monster_id, mythic_id in top:
        if mythic_id is not None:
            notes = "5+4+2+1 A=%s B=%s M=%s Mythic=%s" % (set_a_id, set_b_id, monster_id, mythic_id)
        else:
            notes = "5+5+2 A=%s B=%s M=%s" % (set_a_id, set_b_id, monster_id)
        if use_dph:
            notes += " dph=%.0f" % score
        cur = conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                args.build_id,
                args.class_id,
                args.role_id,
                args.race_id,
                args.mundus_id,
                args.food_id,
                args.potion_id,
                score,
                notes,
            ),
        )
        build_id = cur.lastrowid
        for slot_id, game_id in physical:
            conn.execute(
                """INSERT OR REPLACE INTO recommended_build_equipment (recommended_build_id, slot_id, game_id, game_build_id)
                   VALUES (?, ?, ?, ?)""",
                (build_id, slot_id, game_id, args.build_id),
            )
        ensure_build_class_lines(conn, build_id)
    conn.commit()
    conn.close()
    print("Wrote %s builds to recommended_builds." % len(top))


if __name__ == "__main__":
    main()
