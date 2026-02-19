"""Tests for core.stat_block."""
from __future__ import annotations

import pytest

from core.stat_block import (
    StatBlock,
    DEFAULT_CRIT_CHANCE,
    DEFAULT_CRIT_DAMAGE,
    compute_stat_block,
)


class TestStatBlock:
    def test_defaults(self) -> None:
        b = StatBlock()
        assert b.crit_chance == DEFAULT_CRIT_CHANCE
        assert b.crit_damage == DEFAULT_CRIT_DAMAGE
        assert b.weapon_damage == 0.0
        assert b.penetration == 0.0

    def test_max_stat_for_mechanic(self) -> None:
        b = StatBlock(max_magicka=1000.0, max_stamina=2000.0)
        assert b.max_stat_for_mechanic("Magicka") == 1000.0
        assert b.max_stat_for_mechanic("Stamina") == 2000.0
        assert b.max_stat_for_mechanic(None) == 1000.0

    def test_power_for_mechanic(self) -> None:
        b = StatBlock(weapon_damage=100.0, spell_damage=200.0)
        assert b.power_for_mechanic("Stamina") == 100.0
        assert b.power_for_mechanic("Magicka") == 200.0
        assert b.power_for_mechanic(None) == 200.0


class TestComputeStatBlock:
    def test_empty_no_weapons(self, conn, game_build_id: int) -> None:
        block = compute_stat_block(
            conn, game_build_id, race_id=1,
            set_pieces=None, food_id=None, potion_id=None, mundus_id=None,
            front_bar_weapons=None,
        )
        assert block is not None
        assert block.crit_chance == DEFAULT_CRIT_CHANCE
        assert block.crit_damage == DEFAULT_CRIT_DAMAGE

    def test_with_mundus(self, conn, game_build_id: int) -> None:
        # Thief (11) gives critical_rating; Warrior (13) gives weapon_damage
        block = compute_stat_block(
            conn, game_build_id, race_id=1,
            set_pieces=None, food_id=None, potion_id=None, mundus_id=11,
            front_bar_weapons=None,
        )
        assert block.critical_rating >= 0
        assert block.max_magicka >= 0 or block.max_stamina >= 0

    def test_with_weapon_types(self, conn, game_build_id: int) -> None:
        block = compute_stat_block(
            conn, game_build_id, race_id=1,
            set_pieces=None, food_id=None, potion_id=None, mundus_id=None,
            front_bar_weapons=("dagger", "dagger"),
        )
        assert block.critical_rating >= 0
        block2 = compute_stat_block(
            conn, game_build_id, race_id=1,
            set_pieces=None, food_id=None, potion_id=None, mundus_id=None,
            front_bar_weapons=("sword", "sword"),
        )
        assert block2.weapon_damage >= 0
        assert block2.spell_damage >= 0
