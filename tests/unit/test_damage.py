"""Tests for core.damage."""
from __future__ import annotations

import json
import pytest

from core.stat_block import StatBlock
from core.damage import (
    parse_coefficient_json,
    get_damage_coefficient_slot,
    base_damage_from_coefficient,
    damage_per_hit,
    armor_mitigation_multiplier,
    ARMOR_CONSTANT,
)


class TestParseCoefficientJson:
    def test_empty(self) -> None:
        assert parse_coefficient_json(None) == []
        assert parse_coefficient_json("") == []
        assert parse_coefficient_json("   ") == []

    def test_valid_list(self) -> None:
        data = [{"type": 1, "a": 0.01, "b": 0.5, "c": 10.0}]
        out = parse_coefficient_json(json.dumps(data))
        assert len(out) == 1
        assert out[0]["a"] == 0.01
        assert out[0]["b"] == 0.5
        assert out[0]["c"] == 10.0

    def test_invalid_returns_empty(self) -> None:
        assert parse_coefficient_json("not json") == []
        assert parse_coefficient_json("{}") == []


class TestGetDamageCoefficientSlot:
    def test_no_slot(self) -> None:
        assert get_damage_coefficient_slot(None) is None
        assert get_damage_coefficient_slot("[]") is None

    def test_first_with_ab(self) -> None:
        data = [{"type": 1, "a": 0.01, "b": 0.5, "c": 10.0}]
        slot = get_damage_coefficient_slot(json.dumps(data))
        assert slot is not None
        assert slot["a"] == 0.01


class TestBaseDamageFromCoefficient:
    def test_formula(self) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        coef = {"a": 0.0001, "b": 0.5, "c": 100.0}
        base = base_damage_from_coefficient(block, coef, use_stamina=False)
        expected = 0.0001 * 10000 + 0.5 * 3000 + 100
        assert abs(base - expected) < 1e-6

    def test_stamina_uses_weapon(self) -> None:
        block = StatBlock(max_stamina=8000.0, weapon_damage=2000.0)
        coef = {"a": 0.0, "b": 1.0, "c": 0.0}
        base = base_damage_from_coefficient(block, coef, use_stamina=True)
        assert base == 2000.0


class TestDamagePerHit:
    def test_no_coef_returns_zero(self) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        assert damage_per_hit(block, None, False) == 0.0
        assert damage_per_hit(block, "[]", False) == 0.0

    def test_with_crit_and_mitigation(self) -> None:
        block = StatBlock(
            max_magicka=10000.0, spell_damage=3000.0,
            crit_chance=0.5, crit_damage=0.5, penetration=0.0,
        )
        coef = [{"type": 1, "a": 0.0, "b": 1.0, "c": 0.0}]
        dph = damage_per_hit(
            block, json.dumps(coef), False,
            target_resistance=6600.0, target_damage_taken_pct=0.0,
        )
        assert dph > 0
        base = 3000.0
        crit_mult = 1.0 + block.crit_chance * block.crit_damage
        mitigation = 1.0 / (1.0 + 6600.0 / ARMOR_CONSTANT)
        expected = base * crit_mult * mitigation
        assert abs(dph - expected) < 1.0

    def test_vuln_multiplier(self) -> None:
        block = StatBlock(max_magicka=1000.0, spell_damage=1000.0)
        coef = [{"type": 1, "a": 0.0, "b": 1.0, "c": 0.0}]
        dph_no_vuln = damage_per_hit(
            block, json.dumps(coef), False,
            target_resistance=0.0, target_damage_taken_pct=0.0, include_crit=False,
        )
        dph_vuln = damage_per_hit(
            block, json.dumps(coef), False,
            target_resistance=0.0, target_damage_taken_pct=0.10, include_crit=False,
        )
        assert dph_vuln == pytest.approx(dph_no_vuln * 1.10)


class TestArmorMitigationMultiplier:
    def test_zero_resistance(self) -> None:
        assert armor_mitigation_multiplier(0.0, 0.0) == 1.0

    def test_high_resistance_reduces(self) -> None:
        m = armor_mitigation_multiplier(18200.0, 0.0)
        assert 0.0 < m < 1.0

    def test_penetration_increases_damage(self) -> None:
        m_no_pen = armor_mitigation_multiplier(10000.0, 0.0)
        m_pen = armor_mitigation_multiplier(10000.0, 3000.0)
        assert m_pen > m_no_pen
