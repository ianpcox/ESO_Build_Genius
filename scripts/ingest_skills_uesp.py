"""
Ingest skills and skill coefficients from UESP ESO Log exportJson API (skillCoef table).

skillCoef = subset of minedSkills with numCoefVars > 0: damage/heal formula coefficients.
API: https://esolog.uesp.net/exportJson.php?table=skillCoef&limit=N&offset=M

Maps to skills table: ability_id, name, description, skill_line, class_name, mechanic,
cost, duration_sec, cast_time_sec, coefficient_json (type1..6, a1..c1, R1, avg1, etc.).

Usage:
  python scripts/ingest_skills_uesp.py --build-label "Update 48"
  python scripts/ingest_skills_uesp.py --build-id 1 --replace
  python scripts/ingest_skills_uesp.py --build-label "Update 48" --limit 500 --dry-run

Data sourcing: see docs/DATA_SOURCES.md (Recommendations: UESP retained for skill coefficients; addon API does not expose them).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_DIR, "eso_build_genius.db")
UESP_SKILL_COEF_URL = "https://esolog.uesp.net/exportJson.php"
CHUNK_SIZE = 2000
USER_AGENT = "ESO-Build-Genius/1.0 (https://github.com/)"
# Pagination cap when no --limit: fetch all. skillCoef has ~7k rows (see viewSkillCoef), not 126k (minedSkills).
FETCH_ALL_CAP = 999999
# Expected skillCoef size (UESP viewSkillCoef ~7083). Used for sanity checks; outside range suggests wrong table or API change.
EXPECTED_SKILL_COEF_MIN = 5000
EXPECTED_SKILL_COEF_MAX = 12000


def _int(val, default: int | None = None) -> int | None:
    if val is None or val == "" or val == "-1":
        return default
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _float(val, default: float | None = None) -> float | None:
    if val is None or val == "" or val == "-1":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _str(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _ms_to_sec(ms) -> float | None:
    v = _int(ms)
    if v is None or v <= 0:
        return None
    return v / 1000.0


def build_coefficient_json(rec: dict) -> str | None:
    """Build JSON array of coefficient slots (type, a, b, c, R, avg) for active vars."""
    n = _int(rec.get("numCoefVars"), 0) or 0
    if n <= 0:
        return None
    out = []
    for i in range(1, min(n + 1, 7)):
        t = rec.get(f"type{i}", "-1")
        a, b, c = rec.get(f"a{i}"), rec.get(f"b{i}"), rec.get(f"c{i}")
        R, avg = rec.get(f"R{i}"), rec.get(f"avg{i}")
        if t == "-1" or t is None:
            continue
        out.append({
            "type": _int(t),
            "a": _float(a),
            "b": _float(b),
            "c": _float(c),
            "R": _float(R),
            "avg": _float(avg),
        })
    if not out:
        return None
    return json.dumps(out)


def mechanic_label(base_mechanic) -> str | None:
    """Map baseMechanic code to label (1=Magicka, 4=Stamina, etc.)."""
    m = _int(base_mechanic)
    if m is None:
        return None
    labels = {1: "Magicka", 4: "Stamina", 2: "Ultimate", 3: "Health", 0: "None"}
    return labels.get(m, str(m))


def fetch_skill_coef_chunk(limit: int, offset: int) -> list[dict]:
    url = f"{UESP_SKILL_COEF_URL}?table=skillCoef&limit={limit}&offset={offset}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return data.get("skillCoef") or []


def fetch_all_skill_coef(limit: int | None = None) -> list[dict]:
    """Fetch all skillCoef records via pagination. skillCoef has ~7k rows (UESP viewSkillCoef); FETCH_ALL_CAP is just a pagination cap."""
    out: list[dict] = []
    offset = 0
    max_records = limit or FETCH_ALL_CAP
    while len(out) < max_records:
        chunk = fetch_skill_coef_chunk(min(CHUNK_SIZE, max_records - len(out)), offset)
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < CHUNK_SIZE:
            break
        offset += len(chunk)
        time.sleep(0.3)
    return out[:max_records] if limit else out


def get_or_create_game_build(conn, label: str) -> int:
    cur = conn.execute("SELECT id FROM game_builds WHERE label = ?", (label,))
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute("INSERT INTO game_builds (label) VALUES (?)", (label,))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def ingest_skills(
    conn,
    game_build_id: int,
    records: list[dict],
    *,
    replace: bool = False,
    data_source: str = "esolog_skillCoef",
) -> int:
    if replace:
        conn.execute("DELETE FROM skills WHERE game_build_id = ?", (game_build_id,))
    inserted = 0
    for rec in records:
        ability_id = _int(rec.get("id"))
        if ability_id is None:
            continue
        name = _str(rec.get("name")) or f"Ability_{ability_id}"
        description = _str(rec.get("description"))
        skill_line = _str(rec.get("skillLine"))
        class_name = _str(rec.get("classType"))
        mechanic = mechanic_label(rec.get("baseMechanic"))
        cost = _int(rec.get("cost"))
        duration_sec = _ms_to_sec(rec.get("duration"))
        cast_time_sec = _ms_to_sec(rec.get("castTime"))
        tick_time_sec = _ms_to_sec(rec.get("tickTime"))
        channel_time_sec = _ms_to_sec(rec.get("channelTime"))
        if channel_time_sec is not None and cast_time_sec is None:
            cast_time_sec = channel_time_sec
        coef_json = build_coefficient_json(rec)
        min_range = _int(rec.get("minRange"))
        max_range = _int(rec.get("maxRange"))
        range_text = None
        if max_range is not None and max_range > 0:
            range_text = str(max_range) if min_range in (None, 0) else f"{min_range}-{max_range}"

        conn.execute(
            """
            INSERT OR REPLACE INTO skills (
                game_build_id, ability_id, name, skill_line, skill_line_id, class_name,
                mechanic, description, coefficient_json, cost, duration_sec, cast_time_sec,
                range_text, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_build_id,
                ability_id,
                name,
                skill_line,
                None,
                class_name,
                mechanic,
                description,
                coef_json,
                cost,
                duration_sec,
                cast_time_sec,
                range_text,
                data_source,
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest skills + coefficients from UESP ESO Log skillCoef API")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path")
    ap.add_argument("--build-id", type=int, help="Game build id (or use --build-label)")
    ap.add_argument("--build-label", default="Update 48", help="Game build label (use 'Update 48' for Patch 48; created if missing)")
    ap.add_argument("--replace", action="store_true", help="Replace existing skills for this build")
    ap.add_argument("--limit", type=int, default=None, help="Max number of skills to fetch (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="Fetch only; do not write to DB")
    args = ap.parse_args()

    print("Fetching skillCoef from UESP esolog ...")
    try:
        records = fetch_all_skill_coef(limit=args.limit)
    except Exception as e:
        print(f"Failed to fetch: {e}", file=sys.stderr)
        sys.exit(1)
    n = len(records)
    print(f"Received {n} skill records")
    if n < EXPECTED_SKILL_COEF_MIN:
        print(f"  WARNING: Expected ~7k (skillCoef). Got {n}. Partial fetch or API change?", file=sys.stderr)
    elif n > EXPECTED_SKILL_COEF_MAX:
        print(f"  WARNING: Expected ~7k (skillCoef). Got {n}. Wrong table (e.g. minedSkills)? Failing to protect pipeline.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        if records:
            r = records[0]
            print(f"Sample: id={r.get('id')} name={r.get('name')} numCoefVars={r.get('numCoefVars')}")
        return

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        if args.build_id:
            cur = conn.execute("SELECT id FROM game_builds WHERE id = ?", (args.build_id,))
            if not cur.fetchone():
                print(f"No game_build with id={args.build_id}", file=sys.stderr)
                sys.exit(1)
            game_build_id = args.build_id
        else:
            game_build_id = get_or_create_game_build(conn, args.build_label)
        n = ingest_skills(conn, game_build_id, records, replace=args.replace)
        print(f"Inserted/updated {n} skills for game_build_id={game_build_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
