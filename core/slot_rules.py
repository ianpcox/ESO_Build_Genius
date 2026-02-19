"""
Equipment slot rules for ESO builds.

Standard DD: 12 gear slots = 7 body + 3 jewelry + 2 weapon (front bar, back bar).
We use 14 physical slots (8,9 = front weapons, 10,11 = back weapons); front/back
weapon slots are assigned the same set so piece count stays 5+5+2.

Valid build: two 5-piece sets + one 2-piece monster set. Optional: one mythic (1pc)
replacing one piece of a 5pc set (5+4+2+1).
"""
from __future__ import annotations

import sqlite3
from itertools import combinations, product

# 12 logical slots: 7 body + 3 jewelry + 2 weapon (front=8,9 same set; back=10,11 same set).
BODY_SLOT_IDS = [1, 2, 3, 4, 5, 6, 7]
JEWELRY_SLOT_IDS = [12, 13, 14]
# Weapon: we assign slot 8 (and 9 gets same game_id), slot 10 (and 11 gets same).
LOGICAL_WEAPON_FRONT = 8
LOGICAL_WEAPON_BACK = 10
ALL_LOGICAL_SLOT_IDS = BODY_SLOT_IDS + JEWELRY_SLOT_IDS + [LOGICAL_WEAPON_FRONT, LOGICAL_WEAPON_BACK]

# When writing to recommended_build_equipment, expand weapon slots to both hands.
SLOT_EXPAND_WEAPON: dict[int, list[int]] = {8: [8, 9], 10: [10, 11]}


def get_five_piece_sets(conn: sqlite3.Connection, game_build_id: int) -> list[tuple[int, str]]:
    """Return (game_id, set_name) for sets that are 5-piece and not monster/mythic."""
    cur = conn.execute(
        """
        SELECT game_id, set_name FROM set_summary
        WHERE game_build_id = ? AND set_max_equip_count = 5
          AND type IN ('crafted','dungeon','trial','overland','arena','pvp')
        ORDER BY game_id
        """,
        (game_build_id,),
    )
    return [tuple(row) for row in cur.fetchall()]


def get_monster_sets(conn: sqlite3.Connection, game_build_id: int) -> list[tuple[int, str]]:
    """Return (game_id, set_name) for 2-piece monster sets."""
    cur = conn.execute(
        """
        SELECT game_id, set_name FROM set_summary
        WHERE game_build_id = ? AND type = 'monster' AND set_max_equip_count = 2
        ORDER BY game_id
        """,
        (game_build_id,),
    )
    return [tuple(row) for row in cur.fetchall()]


def get_mythic_sets(conn: sqlite3.Connection, game_build_id: int) -> list[tuple[int, str]]:
    """Return (game_id, set_name) for 1-piece mythic sets."""
    cur = conn.execute(
        """
        SELECT game_id, set_name FROM set_summary
        WHERE game_build_id = ? AND type = 'mythic' AND set_max_equip_count = 1
        ORDER BY game_id
        """,
        (game_build_id,),
    )
    return [tuple(row) for row in cur.fetchall()]


def get_set_slot_ids(conn: sqlite3.Connection, game_build_id: int, game_id: int) -> set[int]:
    """Return slot_ids this set can occupy (from set_item_slots). Includes 8 and 10 for weapons."""
    cur = conn.execute(
        """
        SELECT slot_id FROM set_item_slots
        WHERE game_build_id = ? AND game_id = ?
        """,
        (game_build_id, game_id),
    )
    raw = {row[0] for row in cur.fetchall()}
    # Normalize weapon: if 8 or 9 in raw, allow 8; if 10 or 11 in raw, allow 10.
    out = set()
    for s in raw:
        if s in (8, 9):
            out.add(LOGICAL_WEAPON_FRONT)
        elif s in (10, 11):
            out.add(LOGICAL_WEAPON_BACK)
        else:
            out.add(s)
    return out


def assign_slots(
    conn: sqlite3.Connection,
    game_build_id: int,
    set_a_id: int,
    set_b_id: int,
    monster_id: int,
) -> list[tuple[int, int]] | None:
    """
    Assign 12 logical slots to the three sets (5+5+2). Monster gets head+shoulders (1,2).
    Returns list of (slot_id, game_id) with slot_id in ALL_LOGICAL_SLOT_IDS, or None if impossible.
    """
    slots_a = get_set_slot_ids(conn, game_build_id, set_a_id)
    slots_b = get_set_slot_ids(conn, game_build_id, set_b_id)
    slots_m = get_set_slot_ids(conn, game_build_id, monster_id)

    # Monster must be able to occupy 1 and 2.
    if 1 not in slots_m or 2 not in slots_m:
        return None
    used = {1, 2}
    assignment: list[tuple[int, int]] = [(1, monster_id), (2, monster_id)]

    remaining = set(s for s in ALL_LOGICAL_SLOT_IDS if s not in used)
    avail_a = remaining & slots_a
    avail_b = remaining & slots_b
    if len(avail_a) < 5 or len(avail_b) < 5:
        return None
    # Partition remaining into 5 for A and 5 for B (no overlap).
    for pick_a in combinations(sorted(avail_a), 5):
        pick_a_set = set(pick_a)
        other = remaining - pick_a_set
        pick_b = sorted(s for s in other if s in slots_b)
        if len(pick_b) >= 5:
            for s in pick_a:
                assignment.append((s, set_a_id))
            for s in pick_b[:5]:
                assignment.append((s, set_b_id))
            return assignment
    return None


def assign_slots_mythic(
    conn: sqlite3.Connection,
    game_build_id: int,
    set_a_id: int,
    set_b_id: int,
    monster_id: int,
    mythic_id: int,
) -> list[tuple[int, int]] | None:
    """
    Assign 12 logical slots for 5+4+2+1: set_a 5pc, set_b 4pc, monster 2pc, mythic 1pc.
    Monster gets 1,2; mythic gets one slot from remaining; then 5 for A and 4 for B.
    """
    slots_a = get_set_slot_ids(conn, game_build_id, set_a_id)
    slots_b = get_set_slot_ids(conn, game_build_id, set_b_id)
    slots_m = get_set_slot_ids(conn, game_build_id, monster_id)
    slots_my = get_set_slot_ids(conn, game_build_id, mythic_id)
    if 1 not in slots_m or 2 not in slots_m:
        return None
    used = {1, 2}
    remaining = set(s for s in ALL_LOGICAL_SLOT_IDS if s not in used)
    for mythic_slot in sorted(remaining & slots_my):
        after_mythic = remaining - {mythic_slot}
        avail_a = after_mythic & slots_a
        avail_b = after_mythic & slots_b
        if len(avail_a) < 5 or len(avail_b) < 4:
            continue
        for pick_a in combinations(sorted(avail_a), 5):
            pick_a_set = set(pick_a)
            other = after_mythic - pick_a_set
            pick_b = sorted(s for s in other if s in slots_b)
            if len(pick_b) >= 4:
                assignment = [(1, monster_id), (2, monster_id)]
                for s in pick_a:
                    assignment.append((s, set_a_id))
                for s in pick_b[:4]:
                    assignment.append((s, set_b_id))
                assignment.append((mythic_slot, mythic_id))
                return assignment
    return None


def expand_equipment_to_physical_slots(assignment: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Expand logical (8, game_id) to (8, game_id), (9, game_id); same for 10 -> 10, 11."""
    out: list[tuple[int, int]] = []
    for slot_id, game_id in assignment:
        if slot_id in SLOT_EXPAND_WEAPON:
            for phys in SLOT_EXPAND_WEAPON[slot_id]:
                out.append((phys, game_id))
        else:
            out.append((slot_id, game_id))
    return out


def enumerate_valid_combos(
    conn: sqlite3.Connection,
    game_build_id: int,
    *,
    five_piece_limit: int = 0,
    monster_limit: int = 0,
):
    """
    Yield (set_a_id, set_b_id, monster_id, assignment) for valid 5+5+2 builds.
    assignment is list of (slot_id, game_id) for 12 logical slots.
    If five_piece_limit/monster_limit > 0, only consider that many candidates (for testing).
    """
    fives = get_five_piece_sets(conn, game_build_id)
    monsters = get_monster_sets(conn, game_build_id)
    if five_piece_limit > 0:
        fives = fives[:five_piece_limit]
    if monster_limit > 0:
        monsters = monsters[:monster_limit]
    if not fives or not monsters:
        return
    seen = set()
    for (a_id, _), (b_id, _), (m_id, _) in product(fives, fives, monsters):
        if a_id >= b_id:
            continue
        key = (a_id, b_id, m_id)
        if key in seen:
            continue
        seen.add(key)
        assignment = assign_slots(conn, game_build_id, a_id, b_id, m_id)
        if assignment is not None:
            yield (a_id, b_id, m_id, assignment)


def enumerate_valid_combos_mythic(
    conn: sqlite3.Connection,
    game_build_id: int,
    *,
    five_piece_limit: int = 0,
    monster_limit: int = 0,
    mythic_limit: int = 0,
):
    """
    Yield (set_a_id, set_b_id, monster_id, mythic_id, assignment) for valid 5+4+2+1 builds.
    """
    fives = get_five_piece_sets(conn, game_build_id)
    monsters = get_monster_sets(conn, game_build_id)
    mythics = get_mythic_sets(conn, game_build_id)
    if five_piece_limit > 0:
        fives = fives[:five_piece_limit]
    if monster_limit > 0:
        monsters = monsters[:monster_limit]
    if mythic_limit > 0:
        mythics = mythics[:mythic_limit]
    if not fives or not monsters or not mythics:
        return
    seen = set()
    for (a_id, _), (b_id, _), (m_id, _), (my_id, _) in product(fives, fives, monsters, mythics):
        if a_id >= b_id:
            continue
        key = (a_id, b_id, m_id, my_id)
        if key in seen:
            continue
        seen.add(key)
        assignment = assign_slots_mythic(conn, game_build_id, a_id, b_id, m_id, my_id)
        if assignment is not None:
            yield (a_id, b_id, m_id, my_id, assignment)
