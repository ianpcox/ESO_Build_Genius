"""
Ingest all item sets from UESP ESO Log (esolog.uesp.net) exportJson API into the ESO Build Genius DB.

UESP API: https://esolog.uesp.net/exportJson.php?table=setSummary
Returns setSummary records: gameId, setName, setMaxEquipCount, setBonusCount, setBonusDesc1..12,
itemSlots, type, category, sources.

Usage:
  python scripts/ingest_sets_uesp.py --build-label "Update 48" [--replace]
  python scripts/ingest_sets_uesp.py --build-id 1 --db data/eso_build_genius.db
  python scripts/ingest_sets_uesp.py --build-label "Update 48" --dry-run

Creates or reuses a game_build, then inserts into set_summary, set_bonuses, and set_item_slots (UESP-aligned names).

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: prefer addon export for sets when available; UESP for validation).
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from urllib.request import Request, urlopen

# Project paths
SCRIPT_DIR = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
ROOT_DIR = __import__("os").path.dirname(SCRIPT_DIR)
DATA_DIR = __import__("os").path.join(ROOT_DIR, "data")
DEFAULT_DB = __import__("os").path.join(DATA_DIR, "eso_build_genius.db")
UESP_SET_SUMMARY_URL = "https://esolog.uesp.net/exportJson.php?table=setSummary"

# Our equipment_slots: id -> name (schema 01 + 08)
SLOT_ID_TO_NAME = {
    1: "head",
    2: "shoulders",
    3: "chest",
    4: "legs",
    5: "feet",
    6: "hands",
    7: "waist",
    8: "front_main",
    9: "front_off",
    10: "back_main",
    11: "back_off",
    12: "neck",
    13: "ring1",
    14: "ring2",
}
SLOT_NAME_TO_IDS = {
    "head": [1],
    "shoulders": [2],
    "chest": [3],
    "legs": [4],
    "feet": [5],
    "hands": [6],
    "waist": [7],
    "front_main": [8],
    "front_off": [9],
    "back_main": [10],
    "back_off": [11],
    "neck": [12],
    "ring": [13, 14],
    "ring1": [13],
    "ring2": [14],
    "shield": [9, 11],
}
# Body slots (for "Light(All)", "Medium(All)", "Heavy(All)")
BODY_SLOT_IDS = [1, 2, 3, 4, 5, 6, 7]
# Weapon slots
WEAPON_SLOT_IDS = [8, 9, 10, 11]

# set_types we have in schema
VALID_SET_TYPES = {"crafted", "dungeon", "trial", "overland", "arena", "monster", "mythic", "pvp"}


def parse_item_slots(item_slots: str) -> list[int]:
    """
    Parse UESP itemSlots string into our equipment_slots ids (1-14).
    Examples:
      "Weapons(All) Light(All) Medium(All) Heavy(All) Ring Neck Shield" -> 1..14
      "Medium(Head)" -> [1]
      "Heavy(All) Shield Neck Weapons(All) Ring" -> 1..7, 8..11, 12, 13, 14
    """
    if not (item_slots or item_slots.strip()):
        return []
    out: set[int] = set()
    # Normalize: split on spaces; tokens can be "Weapons(All)", "Light(All)", "Ring", "Neck", "Shield", "Medium(Head)"
    tokens = item_slots.strip().split()
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t == "Ring":
            out.update(SLOT_NAME_TO_IDS["ring"])
            continue
        if t == "Neck":
            out.update(SLOT_NAME_TO_IDS["neck"])
            continue
        if t == "Shield":
            out.update(SLOT_NAME_TO_IDS["shield"])
            continue
        if t == "Weapons(All)" or t == "Weapon(All)":
            out.update(WEAPON_SLOT_IDS)
            continue
        # Weight(Slot) e.g. Light(All), Medium(Head), Heavy(Shoulders)
        m = re.match(r"(?i)^(Light|Medium|Heavy)\((\w+)\)$", t)
        if m:
            slot_part = m.group(2).lower()
            if slot_part == "all":
                out.update(BODY_SLOT_IDS)
            else:
                for name, ids in SLOT_NAME_TO_IDS.items():
                    if name == slot_part or (slot_part + "s" == name):
                        out.update(ids)
                        break
                else:
                    if slot_part in SLOT_NAME_TO_IDS:
                        out.update(SLOT_NAME_TO_IDS[slot_part])
                    elif slot_part == "head":
                        out.add(1)
                    elif slot_part == "shoulders":
                        out.add(2)
                    elif slot_part == "chest":
                        out.add(3)
                    elif slot_part == "legs":
                        out.add(4)
                    elif slot_part == "feet":
                        out.add(5)
                    elif slot_part == "hands":
                        out.add(6)
                    elif slot_part == "waist":
                        out.add(7)
            continue
    return sorted(out)


def infer_set_type(rec: dict) -> str:
    """Map UESP type/category/sources and setMaxEquipCount to our set_types.id."""
    max_pieces = int(rec.get("setMaxEquipCount") or 0)
    raw = " ".join(
        [
            str(rec.get("type") or ""),
            str(rec.get("category") or ""),
            str(rec.get("sources") or ""),
        ]
    ).lower()
    if max_pieces == 1:
        return "mythic" if "mythic" in raw else "monster"
    if max_pieces == 2 and "monster" in raw:
        return "monster"
    if "craft" in raw or "crafted" in raw:
        return "crafted"
    if "dungeon" in raw:
        return "dungeon"
    if "trial" in raw:
        return "trial"
    if "arena" in raw:
        return "arena"
    if "mythic" in raw:
        return "mythic"
    if "pvp" in raw or "cyrodiil" in raw or "battleground" in raw:
        return "pvp"
    if "overland" in raw or "world" in raw:
        return "overland"
    return "overland"


def parse_bonus_pieces(effect_text: str) -> int | None:
    """Extract num_pieces from '(N items)' or '(N perfected items)' at start of effect text. Returns None if not found."""
    if not effect_text or not effect_text.strip():
        return None
    # (2 items), (5 items), (5 perfected items)
    m = re.match(r"^\s*\((\d+)\s+(?:perfected\s+)?items?\)", effect_text.strip(), re.I)
    return int(m.group(1)) if m else None


def get_or_create_game_build(conn: sqlite3.Connection, label: str) -> int:
    """Return game_build id for label; create row if missing."""
    cur = conn.execute("SELECT id FROM game_builds WHERE label = ?", (label,))
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute("INSERT INTO game_builds (label) VALUES (?)", (label,))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def fetch_set_summary() -> list[dict]:
    """Fetch full setSummary from UESP exportJson. Returns list of set records."""
    req = Request(UESP_SET_SUMMARY_URL, headers={"User-Agent": "ESO-Build-Genius/1.0 (https://github.com/)"})
    with urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    if "error" in data:
        raise RuntimeError("UESP API error: " + str(data["error"]))
    return data.get("setSummary") or []


def ingest(
    conn: sqlite3.Connection,
    game_build_id: int,
    sets_list: list[dict],
    *,
    replace: bool = False,
) -> tuple[int, int, int]:
    """
    Insert set_summary, set_bonuses, set_item_slots for the given game_build_id.
    Returns (sets_inserted, bonuses_inserted, slots_inserted).
    If replace=True, delete existing set_summary for this game_build_id first.
    """
    if replace:
        conn.execute("DELETE FROM buff_grants_set_bonus WHERE game_build_id = ?", (game_build_id,))
        conn.execute("DELETE FROM set_item_slots WHERE game_build_id = ?", (game_build_id,))
        conn.execute("DELETE FROM set_bonuses WHERE game_build_id = ?", (game_build_id,))
        conn.execute("DELETE FROM set_summary WHERE game_build_id = ?", (game_build_id,))
    sets_ins = bonuses_ins = slots_ins = 0
    for rec in sets_list:
        try:
            set_id = int(rec.get("gameId") or 0)
        except (TypeError, ValueError):
            continue
        name = (rec.get("setName") or "").strip().replace("'", "''")
        if not name:
            continue
        max_pieces = int(rec.get("setMaxEquipCount") or 0)
        if max_pieces <= 0:
            continue
        set_type = infer_set_type(rec)
        if set_type not in VALID_SET_TYPES:
            set_type = "overland"
        conn.execute(
            "INSERT OR REPLACE INTO set_summary (game_build_id, game_id, set_name, type, set_max_equip_count) VALUES (?, ?, ?, ?, ?)",
            (game_build_id, set_id, name, set_type, max_pieces),
        )
        sets_ins += 1

        for i in range(1, 13):
            key = f"setBonusDesc{i}"
            text = (rec.get(key) or "").strip()
            if not text:
                continue
            num_pieces = parse_bonus_pieces(text)
            if num_pieces is None:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO set_bonuses (game_build_id, game_id, num_pieces, set_bonus_desc, effect_type, magnitude) VALUES (?, ?, ?, ?, NULL, NULL)",
                (game_build_id, set_id, num_pieces, text),
            )
            bonuses_ins += 1

        slot_ids = parse_item_slots(rec.get("itemSlots") or "")
        for slot_id in slot_ids:
            conn.execute(
                "INSERT OR IGNORE INTO set_item_slots (game_build_id, game_id, slot_id) VALUES (?, ?, ?)",
                (game_build_id, set_id, slot_id),
            )
            slots_ins += 1

    conn.commit()
    return (sets_ins, bonuses_ins, slots_ins)


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest item sets from UESP ESO Log setSummary API")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, help="Use this game_build id (if not set, use --build-label)")
    ap.add_argument("--build-label", default="Update 48", help="Game build label (create if missing). Use 'Update 48' for Patch 48 current data.")
    ap.add_argument("--replace", action="store_true", help="Replace existing sets for this build")
    ap.add_argument("--dry-run", action="store_true", help="Fetch and print count only, do not write DB")
    args = ap.parse_args()

    if not args.build_id and not args.build_label:
        print("Specify --build-id or --build-label", file=sys.stderr)
        sys.exit(1)

    print("Fetching setSummary from UESP ...")
    try:
        sets_list = fetch_set_summary()
    except Exception as e:
        print(f"Failed to fetch UESP data: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Received {len(sets_list)} set records")

    if args.dry_run:
        print("Dry run: not writing to DB")
        return

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        if args.build_id:
            game_build_id = args.build_id
            cur = conn.execute("SELECT id FROM game_builds WHERE id = ?", (game_build_id,))
            if not cur.fetchone():
                print(f"No game_build with id={game_build_id}", file=sys.stderr)
                sys.exit(1)
        else:
            game_build_id = get_or_create_game_build(conn, args.build_label)
        a, b, c = ingest(conn, game_build_id, sets_list, replace=args.replace)
        print(f"Inserted: set_summary={a}, set_bonuses={b}, set_item_slots={c}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
