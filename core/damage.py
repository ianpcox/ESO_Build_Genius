"""
Damage formula: (stat block, skill coefficient, target) -> damage per hit/tick.

UESP formula: base = a*MaxStat + b*MaxPower + c (from coefficient_json slot).
Then: average_damage = base * (1 + crit_chance * crit_damage) * (1 + damage_done_pct) * armor_mitigation * (1 + damage_taken_debuff).
"""
from __future__ import annotations

import json
from typing import Any

from .stat_block import StatBlock, STAT_POWER_RATIO


# ESO armor mitigation: damage multiplier = 1 / (1 + effective_armor / ARMOR_CONSTANT).
# Level 50 CP 160: constant often cited as 660 (or 661). Target armor after penetration.
ARMOR_CONSTANT = 660.0


def parse_coefficient_json(coefficient_json: str | None) -> list[dict[str, Any]]:
    """Parse skills.coefficient_json to list of {type, a, b, c, R, avg}."""
    if not coefficient_json or not coefficient_json.strip():
        return []
    try:
        out = json.loads(coefficient_json)
        return out if isinstance(out, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_damage_coefficient_slot(coefficient_json: str | None) -> dict[str, Any] | None:
    """
    Return the first coefficient slot suitable for damage (type often 1 or 2 for direct/DoT).
    UESP: a = MaxStat coefficient, b = MaxPower coefficient, c = constant.
    """
    slots = parse_coefficient_json(coefficient_json)
    for slot in slots:
        t = slot.get("type")
        if t is None:
            continue
        # Type 1/2 are typically damage; use first slot with a or b present.
        if slot.get("a") is not None or slot.get("b") is not None:
            return slot
    return None


def base_damage_from_coefficient(
    stat_block: StatBlock,
    coef: dict[str, Any],
    use_stamina: bool,
) -> float:
    """
    Compute base (pre-crit, pre-mitigation) damage from one coefficient slot.
    Formula: base = a*MaxStat + b*MaxPower + c.
    """
    max_stat = stat_block.max_stat_for_mechanic("Stamina" if use_stamina else "Magicka")
    power = stat_block.power_for_mechanic("Stamina" if use_stamina else "Magicka")
    a = float(coef.get("a") or 0.0)
    b = float(coef.get("b") or 0.0)
    c = float(coef.get("c") or 0.0)
    return a * max_stat + b * power + c


def damage_per_hit(
    stat_block: StatBlock,
    coefficient_json: str | None,
    use_stamina: bool,
    *,
    target_resistance: float | None = None,
    target_damage_taken_pct: float = 0.0,
    include_crit: bool = True,
) -> float:
    """
    Expected damage per hit (or per tick for DoTs).

    Does not use cast_time_sec or duration_sec; those are used in rotation/simulation for timing
    and recast. For DoTs, coefficient is interpreted as one slot (per-tick or total per cast
    depending on data); total DoT per cast = per_tick * (duration_sec / tick_interval_sec) when available.
    target_resistance: target armor (physical/spell); we subtract stat_block.penetration.
    target_damage_taken_pct: e.g. 0.10 for Major Vulnerability (10% more damage taken).
    include_crit: if True, multiply by (1 + crit_chance * crit_damage).
    """
    coef = get_damage_coefficient_slot(coefficient_json)
    if not coef:
        return 0.0
    base = base_damage_from_coefficient(stat_block, coef, use_stamina)
    if base <= 0:
        return 0.0
    # Damage done (buffs on self)
    base *= 1.0 + stat_block.damage_done_pct
    # Crit
    if include_crit:
        base *= 1.0 + stat_block.crit_chance * stat_block.crit_damage
    # Target mitigation
    if target_resistance is not None:
        effective_armor = max(0.0, target_resistance - stat_block.penetration)
        mitigation = 1.0 / (1.0 + effective_armor / ARMOR_CONSTANT)
        base *= mitigation
    # Target damage taken (debuffs on target)
    if target_damage_taken_pct != 0.0:
        base *= 1.0 + target_damage_taken_pct
    return base


def armor_mitigation_multiplier(
    target_resistance: float,
    penetration: float,
    constant: float = ARMOR_CONSTANT,
) -> float:
    """Damage multiplier from armor: 1 / (1 + max(0, resistance - penetration) / constant)."""
    effective = max(0.0, target_resistance - penetration)
    return 1.0 / (1.0 + effective / constant)
