"""Tests for core.subclassing."""
from __future__ import annotations

import pytest

from core.subclassing import (
    MAX_OTHER_CLASS_SLOTS,
    CLASS_LINE_SLOTS,
    validate_subclass_lines,
    count_other_class_slots,
    get_default_class_lines_for_class,
    ensure_build_class_lines,
)


class TestConstants:
    def test_max_other(self) -> None:
        assert MAX_OTHER_CLASS_SLOTS == 2
        assert CLASS_LINE_SLOTS == 3


class TestGetDefaultClassLinesForClass:
    def test_dragonknight_three_lines(self, conn, game_build_id: int) -> None:
        lines = get_default_class_lines_for_class(conn, game_build_id, class_id=1)
        assert len(lines) == 3
        assert lines[0] == (1, 101)
        assert lines[1] == (2, 102)
        assert lines[2] == (3, 103)

    def test_sorcerer(self, conn, game_build_id: int) -> None:
        lines = get_default_class_lines_for_class(conn, game_build_id, class_id=2)
        assert len(lines) == 3
        assert all(slot_ord in (1, 2, 3) for slot_ord, _ in lines)
        line_ids = [lid for _, lid in lines]
        assert 201 in line_ids and 202 in line_ids and 203 in line_ids


class TestValidateSubclassLines:
    def test_missing_build_false(self, conn) -> None:
        assert validate_subclass_lines(conn, 999999) is False

    def test_no_class_lines_valid(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 1, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        assert validate_subclass_lines(conn, bid) is True
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()

    def test_all_base_class_valid(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 1, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for slot_ord, skill_line_id in [(1, 101), (2, 102), (3, 103)]:
            conn.execute(
                """INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id)
                   VALUES (?, ?, ?, ?)""",
                (bid, game_build_id, slot_ord, skill_line_id),
            )
        conn.commit()
        assert validate_subclass_lines(conn, bid) is True
        assert count_other_class_slots(conn, bid) == 0
        conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()

    def test_two_other_class_valid(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 1, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # DK (1) with 101 (DK), 301 (NB), 401 (Templar) = 2 other
        for slot_ord, skill_line_id in [(1, 101), (2, 301), (3, 401)]:
            conn.execute(
                """INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id)
                   VALUES (?, ?, ?, ?)""",
                (bid, game_build_id, slot_ord, skill_line_id),
            )
        conn.commit()
        assert validate_subclass_lines(conn, bid) is True
        assert count_other_class_slots(conn, bid) == 2
        conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()

    def test_three_other_class_invalid(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 1, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # All three from other classes: 301, 401, 501
        for slot_ord, skill_line_id in [(1, 301), (2, 401), (3, 501)]:
            conn.execute(
                """INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id)
                   VALUES (?, ?, ?, ?)""",
                (bid, game_build_id, slot_ord, skill_line_id),
            )
        conn.commit()
        assert validate_subclass_lines(conn, bid) is False
        assert count_other_class_slots(conn, bid) == 3
        conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()


class TestEnsureBuildClassLines:
    def test_inserts_default_when_empty(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 2, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        ensure_build_class_lines(conn, bid)
        conn.commit()
        rows = conn.execute(
            "SELECT slot_ord, skill_line_id FROM recommended_build_class_lines WHERE recommended_build_id = ? ORDER BY slot_ord",
            (bid,),
        ).fetchall()
        assert len(rows) == 3
        assert rows[0][1] == 201 and rows[1][1] == 202 and rows[2][1] == 203
        conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()

    def test_idempotent_when_already_filled(self, conn, game_build_id: int) -> None:
        conn.execute(
            """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
               VALUES (?, 1, 1, 1, 1, 1, 1, 0, 'test')""",
            (game_build_id,),
        )
        bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id) VALUES (?, ?, 1, 101)",
            (bid, game_build_id),
        )
        conn.execute(
            "INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id) VALUES (?, ?, 2, 102)",
            (bid, game_build_id),
        )
        conn.execute(
            "INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id) VALUES (?, ?, 3, 103)",
            (bid, game_build_id),
        )
        conn.commit()
        ensure_build_class_lines(conn, bid)
        n = conn.execute("SELECT COUNT(*) FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,)).fetchone()[0]
        assert n == 3
        conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
        conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
        conn.commit()
