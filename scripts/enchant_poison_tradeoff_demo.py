#!/usr/bin/env python3
"""
Demo: compare weapon enchant (glyph) vs weapon poison impact.

Usage:
  python scripts/enchant_poison_tradeoff_demo.py [--db PATH] [--build-id N] [--glyph 1] [--poison 2]
  python scripts/enchant_poison_tradeoff_demo.py --build-label "Update 48" --glyph 7 --poison 3 --base-dps 80000
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT))

DEFAULT_DB = ROOT / "data" / "eso_build_genius.db"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare weapon glyph vs poison impact")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, help="game_build_id")
    ap.add_argument("--build-label", default="Update 48", help="game_build label if no --build-id")
    ap.add_argument("--glyph", type=int, default=1, help="glyph_id (weapon glyph, e.g. 1=Flame, 7=Weapon Damage)")
    ap.add_argument("--poison", type=int, default=2, help="poison_id (e.g. 2=Damage Health, 3=Vulnerability)")
    ap.add_argument("--target-resistance", type=float, default=18200.0, help="Target armor")
    ap.add_argument("--hits-per-sec", type=float, default=1.0, help="Weapon hits per second (proc rate)")
    ap.add_argument("--base-dps", type=float, default=0.0, help="Rotation DPS (for vulnerability poison value)")
    ap.add_argument("--poison-apps-per-sec", type=float, default=0.5, help="Poison applications per second")
    ap.add_argument("--penetration", type=float, default=6600.0, help="Penetration for mitigation")
    ap.add_argument("--crit-chance", type=float, default=0.50, help="Crit chance")
    ap.add_argument("--crit-damage", type=float, default=0.80, help="Crit damage multiplier")
    args = ap.parse_args()

    if not args.db.is_file():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(args.db))
    build_id = args.build_id
    if build_id is None:
        row = conn.execute("SELECT id FROM game_builds WHERE label = ?", (args.build_label,)).fetchone()
        if not row:
            print(f"No game_build with label {args.build_label!r}", file=sys.stderr)
            conn.close()
            return 1
        build_id = row[0]

    g = conn.execute(
        "SELECT name, effect_json FROM glyphs WHERE game_build_id = ? AND glyph_id = ?",
        (build_id, args.glyph),
    ).fetchone()
    p = conn.execute(
        "SELECT name, duration_sec, effect_json FROM weapon_poisons WHERE game_build_id = ? AND poison_id = ?",
        (build_id, args.poison),
    ).fetchone()
    conn.close()

    if not g:
        print(f"Glyph id {args.glyph} not found for build_id {build_id}", file=sys.stderr)
        return 1
    if not p:
        print(f"Poison id {args.poison} not found for build_id {build_id}", file=sys.stderr)
        return 1

    from core.stat_block import StatBlock
    from core.weapon_enchant_tradeoff import compare_glyph_vs_poison

    stat = StatBlock(
        penetration=args.penetration,
        crit_chance=args.crit_chance,
        crit_damage=args.crit_damage,
    )
    result = compare_glyph_vs_poison(
        g[1],
        p[2],
        p[1],
        stat,
        target_resistance=args.target_resistance,
        hits_per_sec=args.hits_per_sec,
        poison_applications_per_sec=args.poison_apps_per_sec,
        base_dps=args.base_dps,
    )

    print(f"Glyph: {g[0]} (id={args.glyph})")
    print(f"  {result.glyph_impact.description}")
    print(f"  DPS contribution: ~{result.glyph_impact.dps_contribution:.0f}")
    if result.glyph_impact.heal_per_sec:
        print(f"  Heal/sec: ~{result.glyph_impact.heal_per_sec:.0f}")
    if result.glyph_impact.shield_per_sec:
        print(f"  Shield/sec: ~{result.glyph_impact.shield_per_sec:.0f}")
    print()
    print(f"Poison: {p[0]} (id={args.poison})")
    print(f"  {result.poison_impact.description}")
    print(f"  DPS contribution: ~{result.poison_impact.dps_contribution:.0f}")
    if result.poison_impact.damage_taken_pct:
        print(f"  Damage taken: +{result.poison_impact.damage_taken_pct*100:.0f}%")
    print()
    print(f"Recommendation: {result.recommendation}")
    print(f"  {result.note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
