"""
Stat modifier reference: look up values from stat_modifier_reference (ingested from
Standalone Damage Modifiers Calculator xlsx "References for Stats" sheet).

Use for caps, formulas, or display (e.g. crit damage cap, penetration formula).
"""
from __future__ import annotations

import sqlite3
from typing import Any


def get_stat_reference(
    conn: sqlite3.Connection,
    game_build_id: int,
) -> dict[str, list[dict[str, Any]]]:
    """
    Load stat_modifier_reference for the given game build, grouped by category.

    Returns dict: category -> list of {"name", "base_value", "effective_value", "formula_notes"}.
    Categories match ingest (e.g. set_bonus, racial, named_bonus, base_stat, buff_pct,
    resource_modifier, damage_modifier). Use for reference caps or formula notes in
    stat block or damage calculations.
    """
    rows = conn.execute(
        """
        SELECT category, name, base_value, effective_value, formula_notes
        FROM stat_modifier_reference
        WHERE game_build_id = ?
        ORDER BY category, name
        """,
        (game_build_id,),
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for category, name, base_value, effective_value, formula_notes in rows:
        if category not in out:
            out[category] = []
        out[category].append({
            "name": name,
            "base_value": base_value,
            "effective_value": effective_value,
            "formula_notes": formula_notes,
        })
    return out


def get_reference_value_by_name(
    conn: sqlite3.Connection,
    game_build_id: int,
    category: str,
    name: str,
    *,
    prefer_effective: bool = True,
) -> float | None:
    """
    Return base_value or effective_value for the given category and name.
    If prefer_effective is True and effective_value is set, return it; else base_value.
    """
    row = conn.execute(
        """
        SELECT base_value, effective_value
        FROM stat_modifier_reference
        WHERE game_build_id = ? AND category = ? AND name = ?
        """,
        (game_build_id, category, name),
    ).fetchone()
    if not row:
        return None
    base, effective = row[0], row[1]
    if prefer_effective and effective is not None:
        return float(effective)
    if base is not None:
        return float(base)
    return None
