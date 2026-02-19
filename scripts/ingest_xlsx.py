"""
Ingest skills and stat modifier reference from xlsx files into the ESO Build Genius DB.

Usage:
  python scripts/ingest_xlsx.py --build-label "Update 48"
  python scripts/ingest_xlsx.py --build-id 1
  python scripts/ingest_xlsx.py --build-label "Update 48" --db data/eso_build_genius.db

Creates or reuses a game_build by label, then:
  1. Damage Skills (Update 38_39_40).xlsx -> skills (from * Top sheets). For Patch 48 use an xlsx updated for Update 48 when available; see docs/CURRENT_PATCH.md.
  2. Standalone Damage Modifiers Calculator (ESO).xlsx "References for Stats" -> stat_modifier_reference
  3. Standalone Damage Modifiers Calculator (ESO).xlsx "Weapon Comparisons" -> weapon_type_stats (optional)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys

try:
    import pandas as pd
except ImportError:
    print("pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "eso_build_genius.db")
DAMAGE_SKILLS_XLSX = os.path.join(DATA_DIR, "Damage Skills (Update 38_39_40).xlsx")
CALCULATOR_XLSX = os.path.join(DATA_DIR, "Standalone Damage Modifiers Calculator (ESO).xlsx")

# Top sheet name -> class_name for skills
TOP_SHEET_TO_CLASS = {
    "Arcanist Top": "Arcanist",
    "DK Top": "Dragonknight",
    "Necro Top": "Necromancer",
    "NB Top": "Nightblade",
    "Sorc Top": "Sorcerer",
    "Temp Top": "Templar",
    "Warden Top": "Warden",
}

# Weapon Comparisons: xlsx weapon name (normalized) -> canonical weapon_type (must match schema 14)
WEAPON_TYPE_ALIASES: dict[str, str] = {
    "dagger": "dagger",
    "mace": "mace",
    "sword": "sword",
    "axe": "axe",
    "2h_sword": "2h_sword",
    "2h_axe": "2h_axe",
    "2h_mace": "2h_mace",
    "2h_swords": "2h_sword",
    "2h_axes": "2h_axe",
    "2h_maces": "2h_mace",
    "2h sword": "2h_sword",
    "2h axe": "2h_axe",
    "2h mace": "2h_mace",
    "two_handed_sword": "2h_sword",
    "two_handed_axe": "2h_axe",
    "two_handed_mace": "2h_mace",
    "bow": "bow",
    "inferno": "inferno_staff",
    "inferno_staff": "inferno_staff",
    "frost": "frost_staff",
    "frost_staff": "frost_staff",
    "lightning": "lightning_staff",
    "lightning_staff": "lightning_staff",
    "resto": "resto_staff",
    "restoration": "resto_staff",
    "resto_staff": "resto_staff",
    "restoration_staff": "resto_staff",
    "shield": "shield",
}

# References for Stats: section header (col 0 or 4) -> category for DB
STAT_CATEGORY_MAP = {
    "Set Bonuses": "set_bonus",
    "Racial Bonuses": "racial",
    "Named Bonuses": "named_bonus",
    "Base Stats": "base_stat",
    "% Buffs/Debuffs": "buff_pct",
    "Max Resource Modifiers": "resource_modifier",
    "Wpn/Spl Dmg Modifiers": "damage_modifier",
}


def _stable_ability_id(name: str, class_name: str) -> int:
    """Deterministic integer id from skill name + class (for xlsx-sourced skills)."""
    raw = (name.strip() + "|" + (class_name or "")).encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()[:8]
    return int(h, 16) % (2**31)


def get_or_create_game_build(conn: sqlite3.Connection, label: str) -> int:
    """Return game_build id for label; create row if missing."""
    cur = conn.execute("SELECT id FROM game_builds WHERE label = ?", (label,))
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute(
        "INSERT INTO game_builds (label) VALUES (?)",
        (label,),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def _num(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _int_num(val) -> int | None:
    n = _num(val)
    if n is None:
        return None
    return int(n)


def _str(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def ingest_skills_from_damage_xlsx(
    conn: sqlite3.Connection,
    game_build_id: int,
    xlsx_path: str,
    update_label: str | None = None,
) -> int:
    """
    Read Damage Skills xlsx from * Top sheets; insert into skills.
    Returns number of rows inserted.
    """
    if not os.path.isfile(xlsx_path):
        raise FileNotFoundError(f"Damage Skills xlsx not found: {xlsx_path}")

    xl = pd.ExcelFile(xlsx_path)
    inserted = 0
    # Data in Top sheets: header row 2, data from row 4. Cols: 0=Name, 1=Base Tooltip, 2=ADPS, 3=Type, 4=Range, 5=Cost, 6=Time, 7=Crux, 8=Secondary Effect
    for sheet_name in xl.sheet_names:
        if sheet_name not in TOP_SHEET_TO_CLASS:
            continue
        class_name = TOP_SHEET_TO_CLASS[sheet_name]
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)

        for i in range(4, len(df)):
            row = df.iloc[i]
            name = _str(row.iloc[0])
            if not name or name.upper() == "ADPS":
                continue
            base_tooltip = _num(row.iloc[1])
            if base_tooltip is None:
                continue
            adps = _num(row.iloc[2])
            skill_type = _str(row.iloc[3])
            range_text = _str(row.iloc[4])
            cost_raw = row.iloc[5]
            cost = _int_num(cost_raw) if cost_raw is not None else None
            time_val = row.iloc[6]
            duration_sec = _num(time_val)
            cast_time_sec = None
            if duration_sec is not None and 0 < duration_sec < 2 and duration_sec != 1:
                cast_time_sec = duration_sec
                duration_sec = None
            crux = _int_num(row.iloc[7]) if len(row) > 7 else None
            if crux is not None and crux < 0:
                crux = None
            description = _str(row.iloc[8]) if len(row) > 8 else None

            ability_id = _stable_ability_id(name, class_name)
            conn.execute(
                """
                INSERT OR REPLACE INTO skills (
                    game_build_id, ability_id, name, skill_line, class_name,
                    base_tooltip, adps, skill_damage_type, range_text, cost,
                    duration_sec, cast_time_sec, crux_required, description,
                    data_source, update_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_build_id,
                    ability_id,
                    name,
                    None,
                    class_name,
                    base_tooltip,
                    adps,
                    skill_type,
                    range_text,
                    cost,
                    duration_sec,
                    cast_time_sec,
                    crux,
                    description,
                    "damage_skills_xlsx",
                    update_label,
                ),
            )
            inserted += 1

    conn.commit()
    return inserted


def ingest_stat_modifiers_from_calculator(
    conn: sqlite3.Connection,
    game_build_id: int,
    xlsx_path: str,
) -> int:
    """
    Read "References for Stats" sheet; parse sections and insert into stat_modifier_reference.
    Returns number of rows inserted.
    """
    if not os.path.isfile(xlsx_path):
        raise FileNotFoundError(f"Calculator xlsx not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name="References for Stats", header=None)
    inserted = 0
    # Two column blocks: left (0,1,2) and right (4,5,6). Section headers in col 0 or col 4.
    left_cat = None
    right_cat = None
    for i in range(len(df)):
        row = df.iloc[i]
        c0 = _str(row.iloc[0]) if len(row) > 0 else None
        c4 = _str(row.iloc[4]) if len(row) > 4 else None

        if c0 and c0 in STAT_CATEGORY_MAP:
            left_cat = STAT_CATEGORY_MAP[c0]
        if c4 and c4 in STAT_CATEGORY_MAP:
            right_cat = STAT_CATEGORY_MAP[c4]

        def insert_if(name, base_val, effective_val, formula_notes, cat):
            if not name or not cat:
                return
            base = _num(base_val)
            eff = _num(effective_val)
            notes = formula_notes
            if eff is None and effective_val is not None and not (isinstance(effective_val, float) and pd.isna(effective_val)):
                notes = ((notes or "") + " " + str(effective_val).strip()).strip() or None
            conn.execute(
                """
                INSERT OR REPLACE INTO stat_modifier_reference
                (game_build_id, category, name, base_value, effective_value, formula_notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (game_build_id, cat, name, base, eff, _str(notes) or None),
            )
            nonlocal inserted
            inserted += 1

        # Left block: name col0, base col1, effective col2
        name_left = c0
        if name_left and left_cat and name_left not in STAT_CATEGORY_MAP:
            base_left = row.iloc[1] if len(row) > 1 else None
            eff_left = row.iloc[2] if len(row) > 2 else None
            insert_if(name_left, base_left, eff_left, None, left_cat)

        # Right block: name col4, base col5, effective col6
        name_right = c4
        if name_right and right_cat and name_right not in STAT_CATEGORY_MAP:
            base_right = row.iloc[5] if len(row) > 5 else None
            eff_right = row.iloc[6] if len(row) > 6 else None
            insert_if(name_right, base_right, eff_right, None, right_cat)

    conn.commit()
    return inserted


def _normalize_header(cell) -> str:
    s = _str(cell) or ""
    return s.lower().strip().replace(" ", "_").replace("%", "pct")


def ingest_weapon_comparisons_from_calculator(
    conn: sqlite3.Connection,
    game_build_id: int,
    xlsx_path: str,
) -> int:
    """
    Read "Weapon Comparisons" (or "Weapon Comparison") sheet; upsert weapon_type_stats.
    Expects a header row: weapon type name, then optional columns for bonus_wd_sd,
    bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes.
    Returns number of rows upserted.
    """
    if not os.path.isfile(xlsx_path):
        raise FileNotFoundError(f"Calculator xlsx not found: {xlsx_path}")
    xl = pd.ExcelFile(xlsx_path)
    sheet = None
    for name in ("Weapon Comparisons", "Weapon Comparison", "WeaponComparison"):
        if name in xl.sheet_names:
            sheet = name
            break
    if not sheet:
        return 0
    df = pd.read_excel(xlsx_path, sheet_name=sheet, header=0)
    if df.empty or len(df.columns) < 1:
        return 0
    # Map header -> column index (case-insensitive, normalized)
    headers = [_normalize_header(df.columns[i]) for i in range(len(df.columns))]
    def col(name_substr: str) -> int | None:
        for i, h in enumerate(headers):
            if name_substr in h or h in name_substr:
                return i
        return None
    weapon_col = col("weapon") or 0
    wd_col = col("wd") or col("weapon_damage") or col("spell_damage") or col("damage")
    crit_chance_col = col("crit_chance") or col("crit_chance_pct")
    pct_done_col = col("pct_done") or col("crit_damage") or col("critical_damage")
    pen_col = col("penetration") or col("pen")
    crit_rating_col = col("crit_rating") or col("critical_rating")
    notes_col = col("notes")
    inserted = 0
    for _, row in df.iterrows():
        raw_type = _str(row.iloc[weapon_col]) if weapon_col is not None else None
        if not raw_type:
            continue
        key = raw_type.lower().strip().replace(" ", "_").replace("-", "_")
        weapon_type = WEAPON_TYPE_ALIASES.get(key) or key
        bonus_wd_sd = _num(row.iloc[wd_col]) if wd_col is not None else None
        bonus_crit_chance = _num(row.iloc[crit_chance_col]) if crit_chance_col is not None else None
        bonus_pct_done = _num(row.iloc[pct_done_col]) if pct_done_col is not None else None
        bonus_penetration = _num(row.iloc[pen_col]) if pen_col is not None else None
        bonus_crit_rating = _num(row.iloc[crit_rating_col]) if crit_rating_col is not None else None
        notes = _str(row.iloc[notes_col]) if notes_col is not None else None
        conn.execute(
            """
            INSERT OR REPLACE INTO weapon_type_stats
            (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_build_id,
                weapon_type,
                bonus_wd_sd,
                bonus_crit_chance,
                bonus_pct_done,
                bonus_penetration,
                bonus_crit_rating,
                notes,
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def record_ingest_run(
    conn: sqlite3.Connection,
    game_build_id: int,
    source_type: str,
    source_path: str,
) -> None:
    conn.execute(
        "INSERT INTO ingest_runs (game_build_id, source_type, source_path) VALUES (?, ?, ?)",
        (game_build_id, source_type, source_path),
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest skills and stat modifiers from xlsx into ESO Build Genius DB",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-label", type=str, help="Game build label (e.g. 'Update 48'); create if missing")
    group.add_argument("--build-id", type=int, help="Use existing game_build id")
    parser.add_argument("--db", type=str, default=DEFAULT_DB, help="SQLite DB path")
    parser.add_argument("--update-label", type=str, default=None, help="Value for skills.update_label (e.g. 'Update 48')")
    parser.add_argument("--skip-weapon-comparisons", action="store_true", help="Do not ingest Weapon Comparisons sheet")
    args = parser.parse_args()

    if not os.path.isfile(args.db):
        print(f"DB not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)

    if args.build_id is not None:
        game_build_id = args.build_id
        cur = conn.execute("SELECT id, label FROM game_builds WHERE id = ?", (game_build_id,))
        if cur.fetchone() is None:
            print(f"game_build id {game_build_id} not found", file=sys.stderr)
            sys.exit(1)
    else:
        game_build_id = get_or_create_game_build(conn, args.build_label)
        print(f"Using game_build id={game_build_id} label={args.build_label!r}")

    update_label = args.update_label or (args.build_label if hasattr(args, "build_label") and args.build_label else None)

    try:
        n_skills = ingest_skills_from_damage_xlsx(
            conn, game_build_id, DAMAGE_SKILLS_XLSX, update_label=update_label
        )
        print(f"Skills: inserted/updated {n_skills} rows from {os.path.basename(DAMAGE_SKILLS_XLSX)}")
        record_ingest_run(conn, game_build_id, "damage_skills_xlsx", DAMAGE_SKILLS_XLSX)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    try:
        n_refs = ingest_stat_modifiers_from_calculator(conn, game_build_id, CALCULATOR_XLSX)
        print(f"Stat modifiers: inserted/updated {n_refs} rows from References for Stats")
        record_ingest_run(conn, game_build_id, "stat_modifier_reference", CALCULATOR_XLSX)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if not args.skip_weapon_comparisons:
        try:
            n_weapon = ingest_weapon_comparisons_from_calculator(conn, game_build_id, CALCULATOR_XLSX)
            if n_weapon > 0:
                print(f"Weapon comparisons: inserted/updated {n_weapon} rows from Weapon Comparisons")
                record_ingest_run(conn, game_build_id, "weapon_comparisons", CALCULATOR_XLSX)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Weapon Comparisons ingest skipped: {e}", file=sys.stderr)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
