"""Tests for core.stat_reference."""
from __future__ import annotations

import pytest

from core.stat_reference import get_stat_reference, get_reference_value_by_name


class TestGetStatReference:
    def test_empty_when_no_rows(self, conn, game_build_id: int) -> None:
        ref = get_stat_reference(conn, game_build_id)
        assert isinstance(ref, dict)
        assert ref == {} or all(isinstance(v, list) for v in ref.values())

    def test_grouped_by_category(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT OR REPLACE INTO stat_modifier_reference (game_build_id, category, name, base_value, effective_value, formula_notes)
               VALUES (?, 'base_stat', 'Critical Chance', 0.10, 0.10, NULL)""",
            (game_build_id,),
        )
        conn.execute(
            """INSERT OR REPLACE INTO stat_modifier_reference (game_build_id, category, name, base_value, effective_value, formula_notes)
               VALUES (?, 'buff_pct', 'Major Berserk', 0.10, 0.10, NULL)""",
            (game_build_id,),
        )
        conn.commit()
        ref = get_stat_reference(conn, game_build_id)
        assert "base_stat" in ref
        assert "buff_pct" in ref
        names_base = [r["name"] for r in ref["base_stat"]]
        assert "Critical Chance" in names_base
        conn.execute("DELETE FROM stat_modifier_reference WHERE game_build_id = ?", (game_build_id,))
        conn.commit()


class TestGetReferenceValueByName:
    def test_missing_returns_none(self, conn, game_build_id: int) -> None:
        assert get_reference_value_by_name(conn, game_build_id, "x", "y") is None

    def test_returns_effective_prefer_default(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT OR REPLACE INTO stat_modifier_reference (game_build_id, category, name, base_value, effective_value, formula_notes)
               VALUES (?, 'buff_pct', 'Crit Cap', 0.25, 0.25, NULL)""",
            (game_build_id,),
        )
        conn.commit()
        v = get_reference_value_by_name(conn, game_build_id, "buff_pct", "Crit Cap", prefer_effective=True)
        assert v == 0.25
        v2 = get_reference_value_by_name(conn, game_build_id, "buff_pct", "Crit Cap", prefer_effective=False)
        assert v2 == 0.25
        conn.execute("DELETE FROM stat_modifier_reference WHERE game_build_id = ? AND name = 'Crit Cap'", (game_build_id,))
        conn.commit()

    def test_returns_base_when_effective_null(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT OR REPLACE INTO stat_modifier_reference (game_build_id, category, name, base_value, effective_value, formula_notes)
               VALUES (?, 'base_stat', 'Pen', 1000, NULL, NULL)""",
            (game_build_id,),
        )
        conn.commit()
        v = get_reference_value_by_name(conn, game_build_id, "base_stat", "Pen", prefer_effective=True)
        assert v == 1000.0
        conn.execute("DELETE FROM stat_modifier_reference WHERE game_build_id = ? AND name = 'Pen'", (game_build_id,))
        conn.commit()
