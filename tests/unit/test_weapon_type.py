"""Tests for core.weapon_type."""
from __future__ import annotations

import pytest

from core.weapon_type import (
    ONE_HAND_DW_TYPES,
    TWO_HANDED_TYPES,
    STAFF_TYPES,
    is_dual_wield_bar,
    get_weapon_type_weights,
    get_aggregate_weapon_bonuses,
    apply_weapon_bonuses_to_stat_block,
    get_weapon_bonuses_for_bar,
    compare_weapon_loadouts,
)
from core.stat_block import StatBlock


class TestIsDualWieldBar:
    def test_two_daggers(self) -> None:
        assert is_dual_wield_bar("dagger", "dagger") is True

    def test_dagger_mace(self) -> None:
        assert is_dual_wield_bar("dagger", "mace") is True

    def test_dagger_only(self) -> None:
        assert is_dual_wield_bar("dagger", None) is False

    def test_bow_not_dw(self) -> None:
        assert is_dual_wield_bar("bow", None) is False
        assert is_dual_wield_bar("bow", "dagger") is False

    def test_2h_not_dw(self) -> None:
        assert is_dual_wield_bar("2h_sword", None) is False


class TestGetWeaponTypeWeights:
    def test_same_dw_doubled(self) -> None:
        w = get_weapon_type_weights("dagger", "dagger")
        assert w == [("dagger", 2.0)]

    def test_different_dw_halved(self) -> None:
        w = get_weapon_type_weights("dagger", "mace")
        assert set(w) == {("dagger", 0.5), ("mace", 0.5)}

    def test_single_2h(self) -> None:
        w = get_weapon_type_weights("2h_sword", None)
        assert w == [("2h_sword", 1.0)]

    def test_bow(self) -> None:
        w = get_weapon_type_weights("bow", None)
        assert w == [("bow", 1.0)]

    def test_staff(self) -> None:
        w = get_weapon_type_weights("inferno_staff", None)
        assert w == [("inferno_staff", 1.0)]

    def test_empty_main(self) -> None:
        assert get_weapon_type_weights(None, "dagger") == []


class TestGetAggregateWeaponBonuses:
    def test_empty_weights(self, conn, game_build_id: int) -> None:
        out = get_aggregate_weapon_bonuses(conn, game_build_id, [])
        assert out["bonus_wd_sd"] == 0.0
        assert out["bonus_penetration"] == 0.0
        assert out["bonus_crit_rating"] == 0.0

    def test_dagger_dagger(self, conn, game_build_id: int) -> None:
        w = [("dagger", 2.0)]
        out = get_aggregate_weapon_bonuses(conn, game_build_id, w)
        assert out["bonus_crit_rating"] == 657 * 2

    def test_sword_sword(self, conn, game_build_id: int) -> None:
        w = [("sword", 2.0)]
        out = get_aggregate_weapon_bonuses(conn, game_build_id, w)
        assert out["bonus_wd_sd"] == 129 * 2

    def test_dagger_mace_halved(self, conn, game_build_id: int) -> None:
        w = [("dagger", 0.5), ("mace", 0.5)]
        out = get_aggregate_weapon_bonuses(conn, game_build_id, w)
        assert out["bonus_crit_rating"] == pytest.approx(657 * 0.5)
        assert out["bonus_penetration"] == pytest.approx(1487 * 0.5)


class TestApplyWeaponBonusesToStatBlock:
    def test_applies_all(self) -> None:
        block = StatBlock()
        bonuses = {
            "bonus_wd_sd": 100.0,
            "bonus_penetration": 500.0,
            "bonus_crit_rating": 300.0,
            "bonus_pct_done": 0.06,
        }
        apply_weapon_bonuses_to_stat_block(block, bonuses)
        assert block.weapon_damage == 100.0
        assert block.spell_damage == 100.0
        assert block.penetration == 500.0
        assert block.critical_rating == 300.0
        assert block.crit_damage == 0.50 + 0.06


class TestGetWeaponBonusesForBar:
    def test_dagger_dagger(self, conn, game_build_id: int) -> None:
        b = get_weapon_bonuses_for_bar(conn, game_build_id, "dagger", "dagger")
        assert b["bonus_crit_rating"] == 657 * 2

    def test_dagger_mace(self, conn, game_build_id: int) -> None:
        b = get_weapon_bonuses_for_bar(conn, game_build_id, "dagger", "mace")
        assert b["bonus_crit_rating"] == pytest.approx(657 * 0.5)
        assert b["bonus_penetration"] == pytest.approx(1487 * 0.5)


class TestCompareWeaponLoadouts:
    def test_compare_two_loadouts(self, conn, game_build_id: int) -> None:
        a, b = compare_weapon_loadouts(
            conn, game_build_id,
            ("dagger", "dagger"),
            ("dagger", "mace"),
        )
        assert a["bonus_crit_rating"] == 657 * 2
        assert b["bonus_crit_rating"] == pytest.approx(657 * 0.5)
        assert b["bonus_penetration"] == pytest.approx(1487 * 0.5)
