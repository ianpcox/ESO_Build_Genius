"""
Demo: compute stat block and damage per hit for a build.

Usage:
  python scripts/stat_block_damage_demo.py [--db PATH] [--build-id N] [--race-id N] [--mundus-id N] [--ability-id ID]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Project root
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from core.stat_block import compute_stat_block, StatBlock
from core.damage import damage_per_hit, get_damage_coefficient_slot, parse_coefficient_json


DEFAULT_DB = ROOT_DIR / "data" / "eso_build_genius.db"


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute stat block and optional damage per hit")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, default=1, help="game_build_id")
    ap.add_argument("--race-id", type=int, default=1, help="race_id (1=Altmer, 2=Argonian, ...)")
    ap.add_argument("--mundus-id", type=int, default=11, help="mundus_id (11=Thief, 13=Warrior, ...)")
    ap.add_argument("--food-id", type=int, default=None, help="food_id (optional)")
    ap.add_argument("--potion-id", type=int, default=None, help="potion_id (optional)")
    ap.add_argument("--weapon-main", type=str, default=None, help="Main hand weapon type (e.g. dagger, mace, sword, axe) for weapon-type bonuses")
    ap.add_argument("--weapon-off", type=str, default=None, help="Off hand weapon type (dual wield); if different from main, bonuses are halved")
    ap.add_argument("--ability-id", type=int, default=None, help="If set, compute damage per hit for this ability_id")
    ap.add_argument("--stamina", action="store_true", help="Use stamina (weapon) for ability; else magicka")
    ap.add_argument("--target-resistance", type=float, default=6600.0, help="Target armor for mitigation (default 6600)")
    args = ap.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(args.db))
    conn.row_factory = sqlite3.Row

    # Stat block: race + mundus + optional weapon types
    set_pieces: list[tuple[int, int]] = []
    front_bar = (args.weapon_main, args.weapon_off) if (args.weapon_main or args.weapon_off) else None
    block = compute_stat_block(
        conn,
        args.build_id,
        args.race_id,
        set_pieces=set_pieces or None,
        food_id=args.food_id,
        potion_id=args.potion_id,
        mundus_id=args.mundus_id,
        front_bar_weapons=front_bar,
    )

    print("Stat block (race_id=%s, mundus_id=%s):" % (args.race_id, args.mundus_id))
    print("  max_health=%.0f max_magicka=%.0f max_stamina=%.0f" % (block.max_health, block.max_magicka, block.max_stamina))
    print("  weapon_damage=%.0f spell_damage=%.0f" % (block.weapon_damage, block.spell_damage))
    print("  penetration=%.0f" % block.penetration)
    print("  crit_chance=%.2f crit_damage=%.2f damage_done_pct=%.2f critical_rating=%.0f" % (block.crit_chance, block.crit_damage, block.damage_done_pct, block.critical_rating))
    print("  physical_resistance=%.0f spell_resistance=%.0f" % (block.physical_resistance, block.spell_resistance))
    print("  magicka_recovery=%.0f stamina_recovery=%.0f" % (block.magicka_recovery, block.stamina_recovery))

    if args.ability_id is not None:
        row = conn.execute(
            "SELECT name, mechanic, coefficient_json FROM skills WHERE game_build_id = ? AND ability_id = ?",
            (args.build_id, args.ability_id),
        ).fetchone()
        if not row:
            print("Ability %s not found for build %s" % (args.ability_id, args.build_id), file=sys.stderr)
            sys.exit(1)
        name, mechanic, coef_json = row["name"], row["mechanic"], row["coefficient_json"]
        use_stamina = args.stamina or (mechanic == "Stamina")
        dmg = damage_per_hit(
            block,
            coef_json,
            use_stamina,
            target_resistance=args.target_resistance,
            target_damage_taken_pct=0.10,  # e.g. Major Vuln
        )
        print("\nAbility: %s (ability_id=%s)" % (name, args.ability_id))
        print("  Damage per hit (with crit, mitigation, 10%% vuln): %.1f" % dmg)
        slot = get_damage_coefficient_slot(coef_json)
        if slot:
            print("  Coefficient slot: a=%s b=%s c=%s" % (slot.get("a"), slot.get("b"), slot.get("c")))

    conn.close()


if __name__ == "__main__":
    main()
