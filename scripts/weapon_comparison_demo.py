"""
Demo: compare weapon type bonuses for two bar loadouts.

Dual wield rule: same type = full bonus per weapon (doubled); different types = half each.
Example: 2 daggers -> 657*2 crit rating; dagger + mace -> 657/2 crit rating + 1487/2 penetration.

Usage:
  python scripts/weapon_comparison_demo.py [--db PATH] [--build-id N]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from core.weapon_type import compare_weapon_loadouts, get_weapon_type_weights

DEFAULT_DB = ROOT_DIR / "data" / "eso_build_genius.db"


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare weapon type stat bonuses for two loadouts")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, default=1, help="game_build_id")
    args = ap.parse_args()

    if not args.db.exists():
        print("DB not found:", args.db, file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(args.db))

    # Loadout A: 2 daggers | Loadout B: dagger + mace
    loadout_a = ("dagger", "dagger")
    loadout_b = ("dagger", "mace")
    bonuses_a, bonuses_b = compare_weapon_loadouts(conn, args.build_id, loadout_a, loadout_b)

    def fmt(b: dict[str, float]) -> str:
        parts = []
        if b.get("bonus_wd_sd"):
            parts.append("WD/SD +%.0f" % b["bonus_wd_sd"])
        if b.get("bonus_crit_rating"):
            parts.append("crit_rating +%.0f" % b["bonus_crit_rating"])
        if b.get("bonus_penetration"):
            parts.append("pen +%.0f" % b["bonus_penetration"])
        if b.get("bonus_pct_done"):
            parts.append("crit_damage +%.0f%%" % (b["bonus_pct_done"] * 100))
        return ", ".join(parts) if parts else "(none)"

    print("Weapon type comparison (build_id=%s)" % args.build_id)
    print("  Weights A:", get_weapon_type_weights(loadout_a[0], loadout_a[1]))
    print("  Loadout A: %s + %s -> %s" % (loadout_a[0], loadout_a[1], fmt(bonuses_a)))
    print("  Weights B:", get_weapon_type_weights(loadout_b[0], loadout_b[1]))
    print("  Loadout B: %s + %s -> %s" % (loadout_b[0], loadout_b[1], fmt(bonuses_b)))
    conn.close()


if __name__ == "__main__":
    main()
