"""Integration tests: stat block + damage + optimizer + subclassing flow."""
from __future__ import annotations

import pytest

from core.stat_block import compute_stat_block
from core.damage import damage_per_hit
from core.rotation import rotation_dps, fight_duration_sec, TRIAL_DUMMY_HP
from core.slot_rules import enumerate_valid_combos, expand_equipment_to_physical_slots
from core.subclassing import ensure_build_class_lines, validate_subclass_lines


def test_stat_block_into_damage(conn, game_build_id: int) -> None:
    block = compute_stat_block(
        conn, game_build_id, race_id=1,
        set_pieces=None, food_id=None, potion_id=None, mundus_id=11,
        front_bar_weapons=("dagger", "dagger"),
    )
    coef = '[{"type":1,"a":0,"b":1,"c":100}]'
    dph = damage_per_hit(block, coef, False, target_resistance=18200.0)
    assert dph > 0


def test_rotation_dps_into_fight_duration(conn, game_build_id: int) -> None:
    from core.stat_block import StatBlock
    block = StatBlock(max_magicka=10000.0, spell_damage=3000.0)
    conn.execute(
        """INSERT OR REPLACE INTO skills (game_build_id, ability_id, name, coefficient_json, mechanic)
           VALUES (?, 90002, 'IntTest', '[{"type":1,"a":0,"b":1,"c":50}]', 'Magicka')""",
        (game_build_id,),
    )
    conn.commit()
    dps = rotation_dps(conn, game_build_id, block, [(90002, 1.0)], target_resistance=0.0)
    assert dps > 0
    duration = fight_duration_sec(dps, TRIAL_DUMMY_HP)
    assert duration > 0
    conn.execute("DELETE FROM skills WHERE game_build_id = ? AND ability_id = 90002", (game_build_id,))
    conn.commit()


def test_optimizer_flow_writes_builds_with_class_lines(conn, game_build_id: int) -> None:
    from core.stat_block import compute_stat_block
    from core.slot_rules import assign_slots

    combos = list(enumerate_valid_combos(conn, game_build_id, five_piece_limit=3, monster_limit=2))
    if not combos:
        pytest.skip("No set combos in DB")
    set_a, set_b, monster_id, assignment = combos[0]
    physical = expand_equipment_to_physical_slots(assignment)
    set_pieces = [(set_a, 5), (set_b, 5), (monster_id, 2)]
    block = compute_stat_block(
        conn, game_build_id, race_id=1,
        set_pieces=set_pieces, food_id=1, potion_id=1, mundus_id=13,
    )
    assert block.weapon_damage >= 0 or block.spell_damage >= 0

    conn.execute(
        """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, score_notes)
           VALUES (?, 1, 1, 1, 13, 1, 1, 100.0, 'int_test')""",
        (game_build_id,),
    )
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for slot_id, game_id in physical:
        conn.execute(
            """INSERT INTO recommended_build_equipment (recommended_build_id, slot_id, game_id, game_build_id)
               VALUES (?, ?, ?, ?)""",
            (bid, slot_id, game_id, game_build_id),
        )
    ensure_build_class_lines(conn, bid)
    conn.commit()
    assert validate_subclass_lines(conn, bid) is True
    rows = conn.execute(
        "SELECT slot_ord, skill_line_id FROM recommended_build_class_lines WHERE recommended_build_id = ? ORDER BY slot_ord",
        (bid,),
    ).fetchall()
    assert len(rows) == 3
    conn.execute("DELETE FROM recommended_build_equipment WHERE recommended_build_id = ?", (bid,))
    conn.execute("DELETE FROM recommended_build_class_lines WHERE recommended_build_id = ?", (bid,))
    conn.execute("DELETE FROM recommended_builds WHERE id = ?", (bid,))
    conn.commit()
