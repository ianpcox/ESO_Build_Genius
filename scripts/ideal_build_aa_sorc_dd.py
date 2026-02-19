#!/usr/bin/env python3
"""
Produce an ideal-build summary for: Dark Elf (Dunmer) Sorcerer magicka DD, Aetherian Archive.
Uses DB (Update 48) for set names and recommend_sets; narrative for race/class/trial context.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_DB = ROOT_DIR / "data" / "eso_build_genius.db"


def main() -> None:
    db = DEFAULT_DB
    if not db.exists():
        print("DB not found:", db, file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    # Resolve Update 48 build
    row = conn.execute("SELECT id FROM game_builds WHERE label = ?", ("Update 48",)).fetchone()
    if not row:
        print("Update 48 build not found.", file=sys.stderr)
        sys.exit(1)
    build_id = row[0]

    # Trial sets (Aetherian Archive is a trial; trial sets are relevant)
    trial_sets = conn.execute(
        """SELECT set_name, game_id FROM set_summary
           WHERE game_build_id = ? AND type = 'trial' AND set_max_equip_count = 5
           ORDER BY set_name""",
        (build_id,),
    ).fetchall()

    # Magicka DD–oriented trial sets (common meta names)
    mag_trial = [t for t in trial_sets if any(x in t[0].lower() for x in (
        "bahsei", "siroria", "false god", "infallible", "concentrated", "relequen",
        "pearlescent", "lucent", "destructive mage", "healing mage", "moondancer",
        "master architect", "eye of nahviintaas",
    ))]

    # Mundus: Thief (crit) typical for mag DD; mundus_id 11 in seed
    mundus = conn.execute(
        "SELECT name FROM mundus_stones WHERE game_build_id = ? AND mundus_id = 11", (build_id,)
    ).fetchone()
    mundus_name = mundus[0] if mundus else "The Thief (typical mag DD)"

    # Races / classes (from schema)
    race_name = "Dunmer (Dark Elf)"
    class_name = "Sorcerer"

    print("=" * 70)
    print("Ideal build (test case): Dark Elf Sorcerer magicka DD – Aetherian Archive")
    print("=" * 70)
    print()
    print("Character")
    print("  Race:  ", race_name, "(strong magicka and fire damage; good for mag DD)")
    print("  Class: ", class_name)
    print("  Role:  Magicka damage dealer (Patch 48)")
    print()
    print("Content")
    print("  Trial: Aetherian Archive (The Mage, The Warrior, The Serpent)")
    print("  Use:   Single-target and cleave; sustain matters in long fights.")
    print()
    print("Mundus")
    print("  ", mundus_name)
    print()
    print("Set suggestions (from DB – trial sets relevant for AA)")
    for name, gid in mag_trial[:14]:
        print("  -", name, "(game_id=%s)" % gid)
    print()
    print("Notes")
    print("  - Two 5-piece sets + one 2-piece monster set (head + shoulders).")
    print("  - Popular magicka trial sets: Bahsei's Mania, Mantle of Siroria,")
    print("    False God's Devotion (sustain), Infallible Mage (Minor Vulnerability).")
    print("  - Monster: Slimecraw (Minor Berserk), Zaan (single target), or")
    print("    Stormfist / Ilambris for AOE. Optimizer in this project currently")
    print("    cannot enumerate 5+5+2 combos because UESP monster data has head and")
    print("    shoulder as separate set records; use recommend_sets per slot for more.")
    print()
    print("Recommendations per slot: run")
    print("  python scripts/recommend_sets.py --db data/eso_build_genius.db --build-id %s --slot <slot_id> [--abilities ...] [--equipment ...]" % build_id)
    print("  Slot ids: 1=head, 2=shoulders, 3=chest, 4=legs, 5=feet, 6=hands, 7=waist, 12=ring1, 13=ring2, 14=neck, 8,9=front bar, 10,11=back bar.")
    conn.close()


if __name__ == "__main__":
    main()
