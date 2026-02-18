"""
Set recommendations driven by self-buff coverage.

Uses buff_coverage to avoid suggesting sets whose bonuses only duplicate buffs
already provided by the build (slotted abilities, passives, other equipped sets).
Team composition (external buffs from healer/tank) is out of scope for now.

Usage as module:
  from recommendations import get_self_buff_coverage, get_set_recommendations_for_slot
"""
from __future__ import annotations

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from buff_coverage import get_buff_coverage, is_set_redundant_for_buffs


def get_self_buff_coverage(
    conn,
    game_build_id: int,
    ability_ids: list[int] | None = None,
    set_pieces: list[tuple[int, int]] | None = None,
    skill_line_ids: list[int] | None = None,
) -> set[int]:
    """
    Self-buff coverage: buff_ids provided by this build's abilities, set bonuses, and passives.
    Same as get_buff_coverage; name clarifies we do not include external (team) buffs.
    """
    return get_buff_coverage(
        conn,
        game_build_id,
        ability_ids=ability_ids,
        set_pieces=set_pieces,
        skill_line_ids=skill_line_ids,
    )


def _equipment_to_set_pieces(equipment: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Convert list of (slot_id, set_id) to list of (set_id, num_pieces) for coverage."""
    from collections import Counter
    counts: dict[int, int] = Counter()
    for _slot_id, set_id in equipment:
        counts[set_id] += 1
    return [(set_id, count) for set_id, count in counts.items()]


def get_candidate_sets_for_slot(conn, game_build_id: int, slot_id: int) -> list[tuple[int, str, str, int]]:
    """
    Return sets that can go in this slot (from set_slots).
    Returns list of (set_id, name, set_type, max_pieces).
    """
    cur = conn.execute(
        """
        SELECT s.set_id, s.name, s.set_type, s.max_pieces
        FROM item_sets s
        INNER JOIN set_slots sl ON sl.game_build_id = s.game_build_id AND sl.set_id = s.set_id
        WHERE s.game_build_id = ? AND sl.slot_id = ?
        ORDER BY s.name
        """,
        (game_build_id, slot_id),
    )
    return [tuple(row) for row in cur.fetchall()]


def _bonus_tiers_with_buffs(conn, game_build_id: int, set_id: int) -> list[int]:
    """Return num_pieces values for this set that have at least one buff in buff_grants_set_bonus."""
    cur = conn.execute(
        """
        SELECT DISTINCT num_pieces FROM buff_grants_set_bonus
        WHERE game_build_id = ? AND set_id = ?
        ORDER BY num_pieces
        """,
        (game_build_id, set_id),
    )
    return [row[0] for row in cur.fetchall()]


def get_set_recommendations_for_slot(
    conn,
    game_build_id: int,
    slot_id: int,
    ability_ids: list[int] | None = None,
    equipment: list[tuple[int, int]] | None = None,
    skill_line_ids: list[int] | None = None,
) -> list[dict]:
    """
    Recommend sets for the given slot using self-buff coverage.

    equipment: list of (slot_id, set_id) for currently equipped slots (can exclude
    the slot we're recommending for). Used to compute current coverage.

    Returns list of dicts:
      set_id, name, set_type, max_pieces,
      self_buff_coverage_count (int),
      redundant_bonuses (list of num_pieces that only duplicate coverage),
      adding_bonuses (list of num_pieces that add at least one new buff),
      is_fully_redundant (True if every bonus that grants buffs is redundant).
    Sorted by: non-fully-redundant first, then by name.
    """
    set_pieces = _equipment_to_set_pieces(equipment or [])
    coverage = get_self_buff_coverage(
        conn, game_build_id,
        ability_ids=ability_ids,
        set_pieces=set_pieces,
        skill_line_ids=skill_line_ids,
    )
    candidates = get_candidate_sets_for_slot(conn, game_build_id, slot_id)
    out: list[dict] = []
    for set_id, name, set_type, max_pieces in candidates:
        bonus_tiers = _bonus_tiers_with_buffs(conn, game_build_id, set_id)
        redundant_bonuses: list[int] = []
        adding_bonuses: list[int] = []
        for num_pieces in bonus_tiers:
            if is_set_redundant_for_buffs(conn, game_build_id, coverage, set_id, num_pieces):
                redundant_bonuses.append(num_pieces)
            else:
                adding_bonuses.append(num_pieces)
        is_fully_redundant = len(bonus_tiers) > 0 and len(redundant_bonuses) == len(bonus_tiers)
        out.append({
            "set_id": set_id,
            "name": name,
            "set_type": set_type,
            "max_pieces": max_pieces,
            "self_buff_coverage_count": len(coverage),
            "redundant_bonuses": redundant_bonuses,
            "adding_bonuses": adding_bonuses,
            "is_fully_redundant": is_fully_redundant,
        })
    out.sort(key=lambda x: (x["is_fully_redundant"], x["name"]))
    return out


def get_buff_names(conn, game_build_id: int, buff_ids: list[int]) -> dict[int, str]:
    """Return { buff_id: name } for given buff_ids."""
    if not buff_ids:
        return {}
    placeholders = ",".join("?" * len(buff_ids))
    cur = conn.execute(
        f"SELECT buff_id, name FROM buffs WHERE game_build_id = ? AND buff_id IN ({placeholders})",
        [game_build_id] + buff_ids,
    )
    return {row[0]: row[1] for row in cur.fetchall()}
