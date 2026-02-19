"""Tests for core.rotation."""
from __future__ import annotations

import json
import pytest

from core.stat_block import StatBlock
from core.rotation import (
    GCD_SEC,
    TRIAL_DUMMY_HP,
    fight_duration_sec,
    rotation_dps,
    dynamic_rotation_dps,
)


class TestConstants:
    def test_gcd(self) -> None:
        assert GCD_SEC == 1.0

    def test_trial_dummy_hp(self) -> None:
        assert TRIAL_DUMMY_HP == 21_000_000


class TestFightDurationSec:
    def test_zero_dps(self) -> None:
        assert fight_duration_sec(0.0) == 0.0
        assert fight_duration_sec(-1.0) == 0.0

    def test_positive(self) -> None:
        assert fight_duration_sec(1000.0, target_hp=10000.0) == 10.0
        assert fight_duration_sec(100000.0, target_hp=TRIAL_DUMMY_HP) == 210.0


class TestRotationDps:
    def test_empty_weights(self, conn, game_build_id: int) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        dps = rotation_dps(conn, game_build_id, block, [])
        assert dps == 0.0

    def test_missing_ability_skipped(self, conn, game_build_id: int) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        dps = rotation_dps(conn, game_build_id, block, [(99999999, 1.0)])
        assert dps == 0.0

    def test_with_skill(self, conn, game_build_id: int) -> None:
        # Insert a minimal skill so rotation_dps has something to hit
        conn.execute(
            """INSERT OR REPLACE INTO skills (game_build_id, ability_id, name, coefficient_json, mechanic)
               VALUES (?, ?, ?, ?, ?)""",
            (game_build_id, 90001, "TestSkill", '[{"type":1,"a":0,"b":1,"c":100}]', "Magicka"),
        )
        conn.commit()
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        dps = rotation_dps(
            conn, game_build_id, block,
            [(90001, 1.0)],
            target_resistance=0.0,
        )
        assert dps > 0
        conn.execute("DELETE FROM skills WHERE game_build_id = ? AND ability_id = 90001", (game_build_id,))


class TestDynamicRotationDps:
    def test_empty_priority(self, conn, game_build_id: int) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        assert dynamic_rotation_dps(conn, game_build_id, block, []) == 0.0

    def test_missing_ability_skipped(self, conn, game_build_id: int) -> None:
        block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
        total = dynamic_rotation_dps(
            conn, game_build_id, block,
            [(99999999, True)],
            sim_duration_sec=2.0,
        )
        assert total == 0.0
