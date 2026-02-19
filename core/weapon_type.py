"""
Weapon type stats and comparisons.

Applies per-weapon-type bonuses (e.g. Twin Blade and Blunt for Dual Wield) from
weapon_type_stats. When dual wielding two different 1H weapon types, effects
from both apply at half strength; when both hands are the same type, the bonus
is full for each weapon (doubled).
"""
from __future__ import annotations

import sqlite3
from typing import Any

from .stat_block import StatBlock


# 1H types that can be dual wielded (Twin Blade and Blunt). Shield is 1H but not DW.
ONE_HAND_DW_TYPES = frozenset({"dagger", "mace", "sword", "axe"})

# Single-slot weapon types (one weapon, no off-hand).
TWO_HANDED_TYPES = frozenset({"2h_sword", "2h_axe", "2h_mace", "bow"})
STAFF_TYPES = frozenset({"inferno_staff", "frost_staff", "lightning_staff", "resto_staff"})
SHIELD_TYPE = "shield"


def is_dual_wield_bar(main_hand_type: str | None, off_hand_type: str | None) -> bool:
    """True if both hands are 1H DW types (no shield, no 2H)."""
    if not main_hand_type or main_hand_type not in ONE_HAND_DW_TYPES:
        return False
    if off_hand_type is None:
        return False
    return off_hand_type in ONE_HAND_DW_TYPES


def get_weapon_type_weights(
    main_hand_type: str | None,
    off_hand_type: str | None,
) -> list[tuple[str, float]]:
    """
    Return list of (weapon_type, weight) for the given bar.

    - 2H / bow / staff: one type with weight 1.0.
    - Dual wield same type (e.g. 2 daggers): one type with weight 2.0.
    - Dual wield different types: each type with weight 0.5 (effects halved).
    """
    if not main_hand_type:
        return []
    main = main_hand_type.strip().lower()
    off = (off_hand_type or "").strip().lower() or None

    # Single weapon (2H, bow, staff)
    if main in TWO_HANDED_TYPES or main in STAFF_TYPES or main == SHIELD_TYPE:
        return [(main, 1.0)]
    if not off:
        return [(main, 1.0)]

    # Dual wield: both must be 1H DW types
    if main not in ONE_HAND_DW_TYPES or off not in ONE_HAND_DW_TYPES:
        return [(main, 1.0)]

    if main == off:
        return [(main, 2.0)]
    return [(main, 0.5), (off, 0.5)]


def get_aggregate_weapon_bonuses(
    conn: sqlite3.Connection,
    game_build_id: int,
    weighted_types: list[tuple[str, float]],
) -> dict[str, float]:
    """
    Aggregate weapon_type_stats bonuses for the given (weapon_type, weight) list.

    Returns dict: bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration,
    bonus_crit_rating (each is sum of stat * weight over matching rows).
    """
    out: dict[str, float] = {
        "bonus_wd_sd": 0.0,
        "bonus_crit_chance": 0.0,
        "bonus_pct_done": 0.0,
        "bonus_penetration": 0.0,
        "bonus_crit_rating": 0.0,
    }
    if not weighted_types:
        return out

    for weapon_type, weight in weighted_types:
        row = conn.execute(
            """SELECT bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating
               FROM weapon_type_stats WHERE game_build_id = ? AND weapon_type = ?""",
            (game_build_id, weapon_type),
        ).fetchone()
        if not row:
            continue
        wd_sd, crit_chance, pct_done, penetration, crit_rating = row
        if wd_sd is not None:
            out["bonus_wd_sd"] += wd_sd * weight
        if crit_chance is not None:
            out["bonus_crit_chance"] += crit_chance * weight
        if pct_done is not None:
            out["bonus_pct_done"] += pct_done * weight
        if penetration is not None:
            out["bonus_penetration"] += penetration * weight
        if crit_rating is not None:
            out["bonus_crit_rating"] += crit_rating * weight
    return out


def apply_weapon_bonuses_to_stat_block(
    block: StatBlock,
    bonuses: dict[str, float],
) -> None:
    """Apply aggregated weapon type bonuses to a StatBlock (in place)."""
    block.weapon_damage += bonuses.get("bonus_wd_sd", 0.0)
    block.spell_damage += bonuses.get("bonus_wd_sd", 0.0)
    block.penetration += bonuses.get("bonus_penetration", 0.0)
    block.critical_rating += bonuses.get("bonus_crit_rating", 0.0)
    block.crit_damage += bonuses.get("bonus_pct_done", 0.0)
    block.crit_chance += bonuses.get("bonus_crit_chance", 0.0)


def get_weapon_bonuses_for_bar(
    conn: sqlite3.Connection,
    game_build_id: int,
    main_hand_type: str | None,
    off_hand_type: str | None,
) -> dict[str, float]:
    """
    Convenience: get aggregate weapon type bonuses for a bar (main + off hand).
    Uses dual-wield halved rule for different types.
    """
    weights = get_weapon_type_weights(main_hand_type, off_hand_type)
    return get_aggregate_weapon_bonuses(conn, game_build_id, weights)


def compare_weapon_loadouts(
    conn: sqlite3.Connection,
    game_build_id: int,
    loadout_a: tuple[str | None, str | None],
    loadout_b: tuple[str | None, str | None],
) -> tuple[dict[str, float], dict[str, float]]:
    """
    Compare two weapon bar loadouts (each is (main_hand_type, off_hand_type)).
    Returns (bonuses_a, bonuses_b) so caller can diff or apply to stat blocks.
    """
    main_a, off_a = loadout_a
    main_b, off_b = loadout_b
    bonuses_a = get_weapon_bonuses_for_bar(conn, game_build_id, main_a, off_a)
    bonuses_b = get_weapon_bonuses_for_bar(conn, game_build_id, main_b, off_b)
    return bonuses_a, bonuses_b
