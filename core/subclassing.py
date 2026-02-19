"""
Subclassing constraint: at most 2 of the 3 class skill-line slots may be from
a different class than the build's base class (recommended_builds.class_id).

Used when validating or writing recommended_build_class_lines.
"""
from __future__ import annotations

import sqlite3

MAX_OTHER_CLASS_SLOTS = 2
CLASS_LINE_SLOTS = 3


def validate_subclass_lines(conn: sqlite3.Connection, recommended_build_id: int) -> bool:
    """
    Return True if this build's recommended_build_class_lines satisfy the subclass rule:
    at most MAX_OTHER_CLASS_SLOTS (2) of the 3 slots have skill_lines.class_id != build's class_id.

    If the build has no class_line rows, returns True (no subclassing to validate).
    """
    row = conn.execute(
        "SELECT class_id, game_build_id FROM recommended_builds WHERE id = ?",
        (recommended_build_id,),
    ).fetchone()
    if not row:
        return False
    build_class_id, game_build_id = row[0], row[1]
    rows = conn.execute(
        """
        SELECT r.slot_ord, s.class_id
        FROM recommended_build_class_lines r
        INNER JOIN skill_lines s ON s.game_build_id = r.game_build_id AND s.skill_line_id = r.skill_line_id
        WHERE r.recommended_build_id = ? AND r.game_build_id = ?
        """,
        (recommended_build_id, game_build_id),
    ).fetchall()
    if not rows:
        return True
    other_count = sum(1 for _slot_ord, line_class_id in rows if line_class_id is not None and line_class_id != build_class_id)
    return other_count <= MAX_OTHER_CLASS_SLOTS


def count_other_class_slots(conn: sqlite3.Connection, recommended_build_id: int) -> int:
    """Return how many of the 3 class-line slots use a different class than the build. 0 if build not found."""
    row = conn.execute(
        "SELECT class_id, game_build_id FROM recommended_builds WHERE id = ?",
        (recommended_build_id,),
    ).fetchone()
    if not row:
        return 0
    build_class_id, game_build_id = row[0], row[1]
    rows = conn.execute(
        """
        SELECT s.class_id
        FROM recommended_build_class_lines r
        INNER JOIN skill_lines s ON s.game_build_id = r.game_build_id AND s.skill_line_id = r.skill_line_id
        WHERE r.recommended_build_id = ? AND r.game_build_id = ?
        """,
        (recommended_build_id, game_build_id),
    ).fetchall()
    return sum(1 for (line_class_id,) in rows if line_class_id is not None and line_class_id != build_class_id)


def get_default_class_lines_for_class(
    conn: sqlite3.Connection, game_build_id: int, class_id: int
) -> list[tuple[int, int]]:
    """
    Return the 3 class skill-line (slot_ord, skill_line_id) for the given class, in slot order 1..3.
    Used to default recommended_build_class_lines when creating a new build (no subclassing).
    """
    rows = conn.execute(
        """
        SELECT skill_line_id
        FROM skill_lines
        WHERE game_build_id = ? AND class_id = ? AND skill_line_type = 'class'
        ORDER BY skill_line_id
        """,
        (game_build_id, class_id),
    ).fetchall()
    return [(slot_ord, row[0]) for slot_ord, row in enumerate(rows, start=1)]


def ensure_build_class_lines(conn: sqlite3.Connection, recommended_build_id: int) -> None:
    """
    If this build has no recommended_build_class_lines rows, insert the default 3 class lines
    for the build's class_id (no subclassing). Idempotent: does nothing if rows already exist.
    """
    row = conn.execute(
        "SELECT class_id, game_build_id FROM recommended_builds WHERE id = ?",
        (recommended_build_id,),
    ).fetchone()
    if not row:
        return
    class_id, game_build_id = row[0], row[1]
    n = conn.execute(
        "SELECT COUNT(1) FROM recommended_build_class_lines WHERE recommended_build_id = ?",
        (recommended_build_id,),
    ).fetchone()[0]
    if n > 0:
        return
    default = get_default_class_lines_for_class(conn, game_build_id, class_id)
    for slot_ord, skill_line_id in default:
        conn.execute(
            """
            INSERT INTO recommended_build_class_lines (recommended_build_id, game_build_id, slot_ord, skill_line_id)
            VALUES (?, ?, ?, ?)
            """,
            (recommended_build_id, game_build_id, slot_ord, skill_line_id),
        )
