"""
Rotation-aware DPS: static (fixed cycle) and dynamic (priority-based, recast on expiry).

Static model: DPS = sum over abilities of (damage_per_hit(ability) * hits_per_sec(ability)).
Weights = casts per second in a fixed repeating sequence. See docs/COMBAT_TIMING_AND_SIMULATION.md §6.

Dynamic model: at each GCD, cast the highest-priority ability whose DoT/buff has expired, else spammable.
Requires duration_sec per ability (from skills); simulates time step-by-step.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from .damage import damage_per_hit

if TYPE_CHECKING:
    from .stat_block import StatBlock

# Minimum time between ability casts (ESO GCD). See COMBAT_TIMING_AND_SIMULATION.md §1.
GCD_SEC = 1.0

# Target Iron Atronach, Trial (21M HP). duration_sec = TRIAL_DUMMY_HP / dps. See COMBAT_TIMING_AND_SIMULATION.md §10.
TRIAL_DUMMY_HP = 21_000_000


def fight_duration_sec(dps: float, target_hp: float = TRIAL_DUMMY_HP) -> float:
    """Fight duration in seconds for a target with target_hp health and constant dps. Returns 0 if dps <= 0."""
    if dps <= 0:
        return 0.0
    return target_hp / dps


def rotation_dps(
    conn: sqlite3.Connection,
    game_build_id: int,
    stat_block: "StatBlock",
    ability_weights: list[tuple[int, float]],
    *,
    use_stamina: bool = False,
    target_resistance: float | None = None,
    target_damage_taken_pct: float = 0.0,
) -> float:
    """
    Static rotation DPS: sum of (damage_per_hit(ability_id) * hits_per_sec) for each (ability_id, hits_per_sec).
    Weights = casts per second in a fixed cycle. When deriving weights from a real rotation, account for
    cast times (e.g. channeled abilities) and durations (DoT/buff recast interval). See COMBAT_TIMING_AND_SIMULATION.md §7.
    """
    total = 0.0
    for ability_id, weight in ability_weights:
        row = conn.execute(
            "SELECT coefficient_json, mechanic FROM skills WHERE game_build_id = ? AND ability_id = ?",
            (game_build_id, ability_id),
        ).fetchone()
        if not row or not row[0]:
            continue
        use_stam = use_stamina or (row[1] == "Stamina")
        dph = damage_per_hit(
            stat_block,
            row[0],
            use_stam,
            target_resistance=target_resistance,
            target_damage_taken_pct=target_damage_taken_pct,
        )
        total += weight * dph
    return total


def dynamic_rotation_dps(
    conn: sqlite3.Connection,
    game_build_id: int,
    stat_block: "StatBlock",
    priority_list: list[tuple[int, bool]],
    *,
    sim_duration_sec: float = 60.0,
    default_duration_sec: float = 10.0,
    use_stamina: bool = False,
    target_resistance: float | None = None,
    target_damage_taken_pct: float = 0.0,
) -> float:
    """
    Dynamic rotation DPS: at each step, cast the highest-priority ability that has expired, else spammable.
    priority_list: [(ability_id, is_spammable), ...] in priority order (DoTs/buffs first, spammable last).
    Uses skills.duration_sec for recast timing; skills.cast_time_sec for time advance (max(GCD, cast_time_sec)).
    """
    if not priority_list:
        return 0.0

    # Load ability data: coefficient_json, mechanic, duration_sec, cast_time_sec
    ability_info: dict[int, tuple[str, bool, float, float]] = {}
    for ability_id, is_spammable in priority_list:
        if ability_id in ability_info:
            continue
        row = conn.execute(
            "SELECT coefficient_json, mechanic, duration_sec, cast_time_sec FROM skills WHERE game_build_id = ? AND ability_id = ?",
            (game_build_id, ability_id),
        ).fetchone()
        if not row or not row[0]:
            continue
        use_stam = use_stamina or (row[1] == "Stamina")
        dur = default_duration_sec if row[2] is None else float(row[2])
        if is_spammable:
            dur = 0.0
        cast_sec = float(row[3]) if row[3] is not None and row[3] > 0 else 0.0
        ability_info[ability_id] = (row[0], use_stam, dur, cast_sec)

    # Expiry time per ability (when the DoT/buff falls off). Start before t=0 so first cast happens.
    expiry: dict[int, float] = {aid: -1.0 for aid, _ in priority_list if aid in ability_info}

    total_damage = 0.0
    t = 0.0
    while t < sim_duration_sec:
        cast_ability_id: int | None = None
        for ability_id, is_spammable in priority_list:
            if ability_id not in ability_info:
                continue
            _, _, duration_sec, _ = ability_info[ability_id]
            if is_spammable:
                if cast_ability_id is None:
                    cast_ability_id = ability_id
                continue
            if expiry[ability_id] <= t:
                cast_ability_id = ability_id
                break

        step_sec = GCD_SEC
        if cast_ability_id is not None and cast_ability_id in ability_info:
            coef_json, use_stam, duration_sec, cast_time_sec = ability_info[cast_ability_id]
            dph = damage_per_hit(
                stat_block,
                coef_json,
                use_stam,
                target_resistance=target_resistance,
                target_damage_taken_pct=target_damage_taken_pct,
            )
            total_damage += dph
            if duration_sec > 0:
                expiry[cast_ability_id] = t + duration_sec
            if cast_time_sec > 0:
                step_sec = max(GCD_SEC, cast_time_sec)

        t += step_sec

    return total_damage / sim_duration_sec if sim_duration_sec > 0 else 0.0
