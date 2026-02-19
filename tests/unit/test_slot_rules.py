"""Tests for core.slot_rules."""
from __future__ import annotations

import pytest

from core.slot_rules import (
    BODY_SLOT_IDS,
    JEWELRY_SLOT_IDS,
    ALL_LOGICAL_SLOT_IDS,
    SLOT_EXPAND_WEAPON,
    get_five_piece_sets,
    get_monster_sets,
    get_set_slot_ids,
    assign_slots,
    expand_equipment_to_physical_slots,
    enumerate_valid_combos,
)


class TestConstants:
    def test_body_slots(self) -> None:
        assert len(BODY_SLOT_IDS) == 7
        assert 1 in BODY_SLOT_IDS and 7 in BODY_SLOT_IDS

    def test_logical_slots_count(self) -> None:
        assert len(ALL_LOGICAL_SLOT_IDS) == 12

    def test_weapon_expand(self) -> None:
        assert SLOT_EXPAND_WEAPON[8] == [8, 9]
        assert SLOT_EXPAND_WEAPON[10] == [10, 11]


class TestGetFivePieceSets:
    def test_returns_list(self, conn, game_build_id: int) -> None:
        fives = get_five_piece_sets(conn, game_build_id)
        assert isinstance(fives, list)
        # Schema 15 seeds at least set 2 (Example 5pc); 07 seeds Kinras (1)
        assert len(fives) >= 1
        for item in fives:
            assert len(item) == 2
            assert isinstance(item[0], int)
            assert isinstance(item[1], str)


class TestGetMonsterSets:
    def test_returns_list(self, conn, game_build_id: int) -> None:
        monsters = get_monster_sets(conn, game_build_id)
        assert isinstance(monsters, list)
        assert len(monsters) >= 1
        for item in monsters:
            assert len(item) == 2


class TestGetSetSlotIds:
    def test_returns_set(self, conn, game_build_id: int) -> None:
        # Set 2 (Example 5pc) has slots 1-14 in seed 15
        slots = get_set_slot_ids(conn, game_build_id, 2)
        assert isinstance(slots, set)
        assert 8 in slots or 9 in slots
        assert LOGICAL_WEAPON_FRONT in slots or 8 in slots

    def test_monster_head_shoulders(self, conn, game_build_id: int) -> None:
        slots = get_set_slot_ids(conn, game_build_id, 3)
        assert 1 in slots
        assert 2 in slots


class TestAssignSlots:
    def test_valid_combo(self, conn, game_build_id: int) -> None:
        # Sets 1, 2 (five) and 3 (monster) from seed
        assignment = assign_slots(conn, game_build_id, 1, 2, 3)
        assert assignment is not None
        assert len(assignment) == 12
        slot_ids = [a[0] for a in assignment]
        assert 1 in slot_ids and 2 in slot_ids
        game_ids = [a[1] for a in assignment]
        assert 3 in game_ids
        assert 1 in game_ids and 2 in game_ids

class TestExpandEquipmentToPhysicalSlots:
    def test_expands_weapon_slots(self) -> None:
        assignment = [(1, 3), (2, 3), (8, 1), (10, 2)]
        out = expand_equipment_to_physical_slots(assignment)
        slot_ids = [o[0] for o in out]
        assert 8 in slot_ids and 9 in slot_ids
        assert 10 in slot_ids and 11 in slot_ids
        assert len(out) == 6
        assert (8, 1) in out and (9, 1) in out
        assert (10, 2) in out and (11, 2) in out

    def test_body_unchanged(self) -> None:
        assignment = [(1, 1), (2, 1)]
        out = expand_equipment_to_physical_slots(assignment)
        assert out == [(1, 1), (2, 1)]


class TestEnumerateValidCombos:
    def test_yields_tuples(self, conn, game_build_id: int) -> None:
        combos = list(enumerate_valid_combos(conn, game_build_id, five_piece_limit=5, monster_limit=5))
        for c in combos:
            set_a, set_b, monster_id, assignment = c
            assert set_a < set_b
            assert assignment is not None
            assert len(assignment) == 12

    def test_limit_respected(self, conn, game_build_id: int) -> None:
        combos = list(enumerate_valid_combos(conn, game_build_id, five_piece_limit=2, monster_limit=1))
        assert len(combos) <= 2


# Import for test
from core.slot_rules import LOGICAL_WEAPON_FRONT
