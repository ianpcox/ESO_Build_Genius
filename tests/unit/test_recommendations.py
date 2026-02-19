"""Tests for scripts.recommendations (redundancy, set recommendations)."""
from __future__ import annotations

import pytest

from recommendations import (
    is_combo_skipped_for_redundancy,
    get_candidate_sets_for_slot,
    get_self_buff_coverage,
)


class TestIsComboSkippedForRedundancy:
    def test_returns_bool(self, conn, game_build_id: int) -> None:
        skip = is_combo_skipped_for_redundancy(conn, game_build_id, 1, 2, 3)
        assert isinstance(skip, bool)

    def test_no_abilities_no_skill_lines(self, conn, game_build_id: int) -> None:
        skip = is_combo_skipped_for_redundancy(
            conn, game_build_id, 1, 2, 3,
            ability_ids=None, skill_line_ids=None,
        )
        assert isinstance(skip, bool)


class TestGetCandidateSetsForSlot:
    def test_returns_list(self, conn, game_build_id: int) -> None:
        cands = get_candidate_sets_for_slot(conn, game_build_id, slot_id=1)
        assert isinstance(cands, list)
        for c in cands[:3]:
            assert len(c) >= 4
            assert isinstance(c[0], int)
            assert isinstance(c[1], str)


class TestGetSelfBuffCoverage:
    def test_returns_set(self, conn, game_build_id: int) -> None:
        coverage = get_self_buff_coverage(
            conn, game_build_id,
            ability_ids=None,
            set_pieces=[(1, 5)],
            skill_line_ids=None,
        )
        assert isinstance(coverage, set)
        assert all(isinstance(b, int) for b in coverage)
