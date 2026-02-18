"""
Populate buff_grants for abilities: link buffs to the skills that grant them.

Uses a curated mapping (skill name -> buff_id) and optionally parses skills.description
for buff name keywords to add more links. Run after create_db and ingest_xlsx (skills + buffs exist).

Buffs (from 07 seed): 1=Minor Berserk, 2=Major Berserk, 3=Minor Brutality, 4=Major Brutality,
                      5=Minor Force, 6=Major Force.

Usage:
  python scripts/populate_buff_grants.py [--db PATH] [--parse-description]
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_DB = os.path.join(ROOT_DIR, "data", "eso_build_genius.db")

# Curated: skill name (as in skills.name) -> buff_id. Expand as needed.
# buff_id 1=Minor Berserk, 2=Major Berserk, 3=Minor Brutality, 4=Major Brutality, 5=Minor Force, 6=Major Force
ABILITY_GRANTS_BUFF: list[tuple[str, int]] = [
    # Minor Force (5)
    ("Barbed Trap", 5),
    ("Lightweight Beast Trap", 5),
    # Major Berserk (2) - e.g. crit buff / "Always Crits"
    ("*Stampede", 2),
    ("Wrecking Blow", 2),
    # Major Brutality / Major Sorcery (4) - weapon & spell damage
    ("Entropy", 4),
    ("Inspired Scholarship", 4),
    ("Recuperative Treatise", 4),
    ("Venom Arrow", 4),
    ("Shrouded Daggers", 4),
    ("Elemental Weapon", 4),
    ("Crushing Weapon", 4),
    ("Bound Armaments", 4),
    ("Expert Hunter", 4),
    # Minor Brutality / Minor Sorcery (3)
    ("Degeneration", 3),
    ("Structured Entropy", 3),
]


# Keywords in description -> buff_id (for --parse-description). First match wins per skill.
DESCRIPTION_BUFF_KEYWORDS: list[tuple[str, int]] = [
    ("Minor Force", 5),
    ("Major Force", 6),
    ("Major Berserk", 2),
    ("Minor Berserk", 1),
    ("Major Brutality", 4),
    ("Major Sorcery", 4),
    ("Minor Brutality", 3),
    ("Minor Sorcery", 3),
]


def insert_ability_grants(conn: sqlite3.Connection, name: str, buff_id: int) -> int:
    """Insert buff_grants for every (game_build_id, ability_id) where skills.name = name. Returns count inserted."""
    cur = conn.execute(
        """
        SELECT s.game_build_id, s.ability_id
        FROM skills s
        INNER JOIN buffs b ON b.game_build_id = s.game_build_id AND b.buff_id = ?
        WHERE s.name = ?
        """,
        (buff_id, name),
    )
    rows = cur.fetchall()
    inserted = 0
    for (game_build_id, ability_id) in rows:
        try:
            conn.execute(
                """
                INSERT INTO buff_grants (game_build_id, buff_id, grant_type, ability_id, skill_line_id, passive_ord)
                VALUES (?, ?, 'ability', ?, NULL, NULL)
                """,
                (game_build_id, buff_id, ability_id),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # already exists
    return inserted


def populate_from_curated(conn: sqlite3.Connection) -> int:
    total = 0
    for name, buff_id in ABILITY_GRANTS_BUFF:
        total += insert_ability_grants(conn, name, buff_id)
    conn.commit()
    return total


def populate_from_descriptions(conn: sqlite3.Connection) -> int:
    """For each skill with a description, if description contains a keyword, add that buff grant."""
    cur = conn.execute(
        "SELECT game_build_id, ability_id, name, description FROM skills WHERE description IS NOT NULL AND description != ''"
    )
    skills = cur.fetchall()
    inserted = 0
    for (game_build_id, ability_id, name, description) in skills:
        if not description:
            continue
        desc_upper = description.upper()
        for (keyword, buff_id) in DESCRIPTION_BUFF_KEYWORDS:
            if keyword.upper() in desc_upper:
                # Check buff exists for this build
                c = conn.execute(
                    "SELECT 1 FROM buffs WHERE game_build_id = ? AND buff_id = ?",
                    (game_build_id, buff_id),
                )
                if c.fetchone() is None:
                    continue
                try:
                    conn.execute(
                        """
                        INSERT INTO buff_grants (game_build_id, buff_id, grant_type, ability_id, skill_line_id, passive_ord)
                        VALUES (?, ?, 'ability', ?, NULL, NULL)
                        """,
                        (game_build_id, buff_id, ability_id),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
                break  # one buff per skill from description
    conn.commit()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate buff_grants for abilities")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--parse-description", action="store_true", help="Also link from skills.description keywords")
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    n_curated = populate_from_curated(conn)
    print(f"Curated mapping: inserted {n_curated} buff_grants (ability -> buff).")

    if args.parse_description:
        n_desc = populate_from_descriptions(conn)
        print(f"From descriptions: inserted {n_desc} buff_grants.")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
