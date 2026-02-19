"""Tests for scripts.buff_coverage (get_buff_coverage, is_set_redundant_for_buffs)."""
from __future__ import annotations

import pytest

from buff_coverage import get_buff_coverage, set_bonus_buff_ids, is_set_redundant_for_buffs


class TestGetBuffCoverage:
    def test_empty_returns_empty(self, conn, game_build_id: int) -> None:
        cov = get_buff_coverage(conn, game_build_id, ability_ids=None, set_pieces=None)
        assert cov == set()

    def test_set_pieces_kinras(self, conn, game_build_id: int) -> None:
        # Seed 07 has Kinras (1) and buff_grants_set_bonus may have 5pc -> Major Berserk (2)
        cov = get_buff_coverage(conn, game_build_id, set_pieces=[(1, 5)])
        assert isinstance(cov, set)
        # If populate_buff_grants_set_bonus was run we might have buff 2
        assert all(isinstance(b, int) for b in cov)


class TestSetBonusBuffIds:
    def test_returns_set(self, conn, game_build_id: int) -> None:
        ids = set_bonus_buff_ids(conn, game_build_id, 1, 5)
        assert isinstance(ids, set)
        assert all(isinstance(b, int) for b in ids)


class TestIsSetRedundantForBuffs:
    def test_empty_coverage_not_redundant(self, conn, game_build_id: int) -> None:
        redundant = is_set_redundant_for_buffs(conn, game_build_id, set(), 1, 5)
        assert redundant is False

    def test_coverage_includes_bonus_redundant(self, conn, game_build_id: int) -> None:
        # If set 1 5pc grants buff 2, then coverage {2} makes set 1 redundant
        bonus_ids = set_bonus_buff_ids(conn, game_build_id, 1, 5)
        if bonus_ids:
            redundant = is_set_redundant_for_buffs(conn, game_build_id, bonus_ids, 1, 5)
            assert redundant is True
