"""
Build a mapping (skill_name -> skill_line_id) from the Damage Skills xlsx class sheets
(which have block headers like ARCANIST, DESTRUCTION, FIGHTERS GUILD), then UPDATE skills
to set skill_line_id (and skill_line text) for all matching skills.

Run after create_db (so skill_lines exist) and after ingest_xlsx (so skills exist).
Usage:
  python scripts/link_skills_to_skill_lines.py [--db PATH] [--xlsx PATH]
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

try:
    import pandas as pd
except ImportError:
    print("pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "eso_build_genius.db")
DAMAGE_SKILLS_XLSX = os.path.join(DATA_DIR, "Damage Skills (Update 38_39_40).xlsx")

# Block header (from xlsx) -> skill_line_id. Class blocks use first line of that class (101, 201, ... 701).
SECTION_TO_SKILL_LINE_ID = {
    "ARCANIST": 701,
    "DRAGONKNIGHT": 101,
    "SORCERER": 201,
    "NIGHTBLADE": 301,
    "TEMPLAR": 401,
    "WARDEN": 501,
    "NECROMANCER": 601,
    "TWO HANDED": 802,
    "DUAL WIELD": 803,
    "BOW": 804,
    "DESTRUCTION": 801,
    "FIGHTERS GUILD": 805,
    "MAGES GUILD": 806,
    "UNDAUNTED": 807,
    "SOUL MAGIC": 808,
    "PSIJIC ORDER": 809,
    "ASSAULT": 810,
}

# Sheets that have the 3-block layout (class name, not "Class Top")
CLASS_SHEETS = [
    "Arcanist", "Dragonknight", "Necromancer", "Nightblade", "Sorcerer", "Templar", "Warden",
]
# Some sheets may be "DK" not "Dragonknight"
if "Dragonknight" not in CLASS_SHEETS:
    pass
# xlsx has "Dragonknight" per inspect output


def _str(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _is_numeric(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def _normalize_header(cell: str) -> str | None:
    if not cell:
        return None
    # Uppercase, collapse spaces
    s = re.sub(r"\s+", " ", str(cell).strip().upper())
    return s if s else None


def build_skill_name_to_line_id(xlsx_path: str) -> dict[str, int]:
    """
    Parse class sheets (not Top). Each sheet has 3 column blocks (0-8, 9-17, 18-26).
    In each block, a row with col in (0, 9, 18) may be a section header or a skill name.
    If it's a known section header (all caps, in SECTION_TO_SKILL_LINE_ID), set current section.
    If the next column (base tooltip) is numeric, it's a skill -> record (name, current_section).
    Returns dict skill_name -> skill_line_id (last occurrence wins for duplicates).
    """
    xl = pd.ExcelFile(xlsx_path)
    name_to_line: dict[str, int] = {}
    block_cols = [0, 9, 18]  # first column of each block

    for sheet_name in xl.sheet_names:
        if sheet_name not in CLASS_SHEETS and sheet_name != "DK":
            continue
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)
        current_section: list[int | None] = [None, None, None]  # per block

        for i in range(2, len(df)):
            row = df.iloc[i]
            for bi, col in enumerate(block_cols):
                cell = _str(row.iloc[col]) if col < len(row) else None
                if not cell:
                    continue
                header_norm = _normalize_header(cell)
                if header_norm and header_norm in SECTION_TO_SKILL_LINE_ID:
                    current_section[bi] = SECTION_TO_SKILL_LINE_ID[header_norm]
                    continue
                # Check if this looks like a skill: next column is base tooltip (numeric)
                next_col = col + 1
                if next_col >= len(row):
                    continue
                base_val = row.iloc[next_col]
                if not _is_numeric(base_val):
                    continue
                # Skip section headers that are all caps and multi-word (already handled above)
                if header_norm and len(cell) > 2 and cell == cell.upper() and " " not in cell.strip():
                    # Could be a short header like "BOW" - but BOW is in our map. So we already handled it.
                    continue
                # This row is a skill name in this block
                section = current_section[bi]
                if section is not None:
                    name_to_line[cell.strip()] = section

    return name_to_line


def link_skills(conn: sqlite3.Connection, name_to_line_id: dict[str, int]) -> int:
    """
    Update skills.skill_line_id and skills.skill_line for all skills whose name is in the mapping.
    Only updates where the skill_line_id exists in skill_lines for that game_build_id.
    Returns number of skill rows updated.
    """
    total_updated = 0
    for name, line_id in name_to_line_id.items():
        cur = conn.execute(
            """
            UPDATE skills SET
                skill_line_id = ?,
                skill_line = (SELECT sl.name FROM skill_lines sl WHERE sl.game_build_id = skills.game_build_id AND sl.skill_line_id = ?)
            WHERE skills.name = ?
              AND EXISTS (SELECT 1 FROM skill_lines sl WHERE sl.game_build_id = skills.game_build_id AND sl.skill_line_id = ?)
            """,
            (line_id, line_id, name, line_id),
        )
        total_updated += cur.rowcount
    conn.commit()
    return total_updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Link skills to skill lines using xlsx class sheets")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--xlsx", default=DAMAGE_SKILLS_XLSX, help="Damage Skills xlsx path")
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.xlsx):
        print(f"Xlsx not found: {args.xlsx}", file=sys.stderr)
        sys.exit(1)

    name_to_line = build_skill_name_to_line_id(args.xlsx)
    print(f"Built mapping for {len(name_to_line)} skill names from class sheets.")

    conn = sqlite3.connect(args.db)
    updated = link_skills(conn, name_to_line)
    conn.close()

    print(f"Updated skill_line_id and skill_line for {updated} skill rows.")


if __name__ == "__main__":
    main()
