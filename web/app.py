"""
ESO Build Genius – Web UI backend.
Serves static frontend and JSON API for build form, equipment slots, and Advisor recommendations.

Run from project root: python web/app.py
Then open http://127.0.0.1:5000/
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sqlite3
from flask import Flask, jsonify, request, send_from_directory

DEFAULT_DB = ROOT / "data" / "eso_build_genius.db"
app = Flask(__name__, static_folder="static", static_url_path="")


@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        from flask import Response
        r = Response(status=204)
        r.headers["Access-Control-Allow-Origin"] = "*"
        r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return r


@app.after_request
def cors_headers(response):
    """Allow Expo Go and other mobile clients on the LAN to call the API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def get_db():
    path = os.environ.get("ESO_BUILD_GENIUS_DB") or str(DEFAULT_DB)
    if not os.path.isfile(path):
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_build_id(conn, label: str = "Update 48"):
    row = conn.execute("SELECT id FROM game_builds WHERE label = ?", (label,)).fetchone()
    return row[0] if row else None


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/build", methods=["GET"])
def api_build_get():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        game_build_id = get_build_id(conn)
        if game_build_id is None:
            return jsonify({"error": "Update 48 build not found"}), 404
        recommended_build_id = request.args.get("recommended_build_id", type=int)
        if recommended_build_id is None:
            return jsonify({"build_id": game_build_id})
        row = conn.execute(
            "SELECT id, game_build_id, class_id, race_id, role_id, mundus_id, food_id, potion_id FROM recommended_builds WHERE id = ? AND game_build_id = ?",
            (recommended_build_id, game_build_id),
        ).fetchone()
        if not row:
            return jsonify({"error": "Build not found"}), 404
        out = {
            "build_id": game_build_id,
            "recommended_build_id": row[0],
            "class_id": row[2],
            "race_id": row[3],
            "role_id": row[4],
            "mundus_id": row[5],
            "food_id": row[6],
            "potion_id": row[7],
        }
        eq = conn.execute(
            "SELECT slot_id, game_id FROM recommended_build_equipment WHERE recommended_build_id = ? ORDER BY slot_id",
            (recommended_build_id,),
        ).fetchall()
        out["equipment"] = [{"slot_id": r[0], "game_id": r[1]} for r in eq]
        bar = conn.execute(
            "SELECT bar_slot_ord, ability_id, scribe_effect_id_1, scribe_effect_id_2, scribe_effect_id_3 FROM recommended_build_scribed_skills WHERE recommended_build_id = ? ORDER BY bar_slot_ord",
            (recommended_build_id,),
        ).fetchall()
        out["bar_skills"] = [
            {
                "bar_slot_ord": r[0],
                "ability_id": r[1],
                "scribe_effect_id_1": r[2],
                "scribe_effect_id_2": r[3],
                "scribe_effect_id_3": r[4],
            }
            for r in bar
        ]
        return jsonify(out)
    finally:
        conn.close()


@app.route("/api/build", methods=["POST"])
def api_build_post():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        data = request.get_json(force=True, silent=True) or {}
        game_build_id = data.get("build_id") or data.get("game_build_id")
        if not game_build_id:
            return jsonify({"error": "build_id required"}), 400
        game_build_id = int(game_build_id)
        recommended_build_id = data.get("recommended_build_id")
        bar_skills = data.get("bar_skills")
        if not isinstance(bar_skills, list):
            return jsonify({"error": "bar_skills must be an array"}), 400

        is_update = recommended_build_id is not None
        if is_update:
            recommended_build_id = int(recommended_build_id)
            row = conn.execute(
                "SELECT id FROM recommended_builds WHERE id = ? AND game_build_id = ?",
                (recommended_build_id, game_build_id),
            ).fetchone()
            if not row:
                return jsonify({"error": "Build not found"}), 404
        else:
            for key in ("class_id", "race_id", "role_id", "mundus_id", "food_id", "potion_id"):
                if data.get(key) is None:
                    return jsonify({"error": f"{key} required when creating a new build"}), 400
            conn.execute(
                """INSERT INTO recommended_builds (game_build_id, class_id, race_id, role_id, mundus_id, food_id, potion_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    game_build_id,
                    int(data["class_id"]),
                    int(data["race_id"]),
                    int(data["role_id"]),
                    int(data["mundus_id"]),
                    int(data["food_id"]),
                    int(data["potion_id"]),
                ),
            )
            recommended_build_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            equipment = data.get("equipment")
            if isinstance(equipment, list):
                for item in equipment:
                    sid = item.get("slot_id")
                    gid = item.get("game_id")
                    if sid is not None and gid is not None:
                        conn.execute(
                            "INSERT INTO recommended_build_equipment (recommended_build_id, game_build_id, slot_id, game_id) VALUES (?, ?, ?, ?)",
                            (recommended_build_id, game_build_id, int(sid), int(gid)),
                        )

        if is_update and data.get("class_id") is not None:
            conn.execute(
                """UPDATE recommended_builds SET class_id = ?, race_id = ?, role_id = ?, mundus_id = ?, food_id = ?, potion_id = ? WHERE id = ?""",
                (
                    int(data["class_id"]),
                    int(data["race_id"]),
                    int(data["role_id"]),
                    int(data["mundus_id"]),
                    int(data["food_id"]),
                    int(data["potion_id"]),
                    recommended_build_id,
                ),
            )
        if is_update:
            equipment = data.get("equipment")
            if isinstance(equipment, list):
                conn.execute("DELETE FROM recommended_build_equipment WHERE recommended_build_id = ?", (recommended_build_id,))
                for item in equipment:
                    sid = item.get("slot_id")
                    gid = item.get("game_id")
                    if sid is not None and gid is not None:
                        conn.execute(
                            "INSERT INTO recommended_build_equipment (recommended_build_id, game_build_id, slot_id, game_id) VALUES (?, ?, ?, ?)",
                            (recommended_build_id, game_build_id, int(sid), int(gid)),
                        )

        conn.execute("DELETE FROM recommended_build_scribed_skills WHERE recommended_build_id = ?", (recommended_build_id,))
        for item in bar_skills:
            ord_val = item.get("bar_slot_ord")
            ability_id = item.get("ability_id")
            if ord_val is None or ability_id is None:
                continue
            ord_val = int(ord_val)
            ability_id = int(ability_id)
            if not (1 <= ord_val <= 12):
                continue
            e1 = item.get("scribe_effect_id_1")
            e2 = item.get("scribe_effect_id_2")
            e3 = item.get("scribe_effect_id_3")
            conn.execute(
                """INSERT INTO recommended_build_scribed_skills (recommended_build_id, game_build_id, bar_slot_ord, ability_id, scribe_effect_id_1, scribe_effect_id_2, scribe_effect_id_3)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (recommended_build_id, game_build_id, ord_val, ability_id, e1 and int(e1) or None, e2 and int(e2) or None, e3 and int(e3) or None),
            )
        conn.commit()
        return jsonify({"recommended_build_id": recommended_build_id})
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/classes")
def api_classes():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute("SELECT id, name FROM classes ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/races")
def api_races():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute("SELECT id, name FROM races ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/roles")
def api_roles():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute("SELECT id, name FROM roles ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/mundus")
def api_mundus():
    build_id = request.args.get("build_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            "SELECT mundus_id, name FROM mundus_stones WHERE game_build_id = ? ORDER BY mundus_id",
            (build_id,),
        ).fetchall()
        return jsonify([{"mundus_id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/foods")
def api_foods():
    build_id = request.args.get("build_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            "SELECT food_id, name FROM foods WHERE game_build_id = ? ORDER BY name LIMIT 600",
            (build_id,),
        ).fetchall()
        return jsonify([{"food_id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/potions")
def api_potions():
    build_id = request.args.get("build_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            "SELECT potion_id, name FROM potions WHERE game_build_id = ? ORDER BY name",
            (build_id,),
        ).fetchall()
        return jsonify([{"potion_id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/slots")
def api_slots():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute("SELECT id, name FROM equipment_slots ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/sets")
def api_sets():
    build_id = request.args.get("build_id", type=int)
    slot_id = request.args.get("slot_id", type=int)
    if not build_id or not slot_id:
        return jsonify({"error": "build_id and slot_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            """
            SELECT s.game_id, s.set_name, s.type, s.set_max_equip_count
            FROM set_summary s
            INNER JOIN set_item_slots sl ON sl.game_build_id = s.game_build_id AND sl.game_id = s.game_id
            WHERE s.game_build_id = ? AND sl.slot_id = ?
            ORDER BY s.set_name
            """,
            (build_id, slot_id),
        ).fetchall()
        return jsonify([
            {"game_id": r[0], "set_name": r[1], "type": r[2], "set_max_equip_count": r[3]}
            for r in rows
        ])
    finally:
        conn.close()


@app.route("/api/scribe_effect_slots")
def api_scribe_effect_slots():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute("SELECT id, name FROM scribe_effect_slots ORDER BY id").fetchall()
        return jsonify([{"id": r[0], "name": r[1]} for r in rows])
    finally:
        conn.close()


@app.route("/api/scribe_effects")
def api_scribe_effects():
    build_id = request.args.get("build_id", type=int)
    ability_id = request.args.get("ability_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        if ability_id is not None:
            has_compat = conn.execute(
                "SELECT 1 FROM skill_scribe_compatibility WHERE game_build_id = ? AND ability_id = ? LIMIT 1",
                (build_id, ability_id),
            ).fetchone()
            if has_compat:
                rows = conn.execute(
                    """
                    SELECT e.scribe_effect_id, e.name, e.slot_id, s.name AS slot_name
                    FROM scribe_effects e
                    JOIN scribe_effect_slots s ON s.id = e.slot_id
                    INNER JOIN skill_scribe_compatibility c ON c.game_build_id = e.game_build_id AND c.scribe_effect_id = e.scribe_effect_id AND c.ability_id = ?
                    WHERE e.game_build_id = ?
                    ORDER BY e.slot_id, e.name
                    """,
                    (ability_id, build_id),
                ).fetchall()
                return jsonify([
                    {"scribe_effect_id": r[0], "name": r[1], "slot_id": r[2], "slot_name": r[3]}
                    for r in rows
                ])
        rows = conn.execute(
            """
            SELECT e.scribe_effect_id, e.name, e.slot_id, s.name AS slot_name
            FROM scribe_effects e
            JOIN scribe_effect_slots s ON s.id = e.slot_id
            WHERE e.game_build_id = ?
            ORDER BY e.slot_id, e.name
            """,
            (build_id,),
        ).fetchall()
        return jsonify([
            {"scribe_effect_id": r[0], "name": r[1], "slot_id": r[2], "slot_name": r[3]}
            for r in rows
        ])
    finally:
        conn.close()


@app.route("/api/skills_for_bar")
def api_skills_for_bar():
    build_id = request.args.get("build_id", type=int)
    class_id = request.args.get("class_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        if class_id:
            rows = conn.execute(
                """
                SELECT DISTINCT sk.ability_id, sk.name, sk.skill_line_id, sl.name AS skill_line_name
                FROM skills sk
                LEFT JOIN skill_lines sl ON sl.game_build_id = sk.game_build_id AND sl.skill_line_id = sk.skill_line_id
                WHERE sk.game_build_id = ?
                  AND (sk.skill_line_id IS NULL OR sl.class_id IS NULL OR sl.class_id = ?)
                ORDER BY sl.name, sk.name
                LIMIT 800
                """,
                (build_id, class_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT sk.ability_id, sk.name, sk.skill_line_id, sl.name AS skill_line_name
                FROM skills sk
                LEFT JOIN skill_lines sl ON sl.game_build_id = sk.game_build_id AND sl.skill_line_id = sk.skill_line_id
                WHERE sk.game_build_id = ?
                ORDER BY sk.name
                LIMIT 800
                """,
                (build_id,),
            ).fetchall()
        return jsonify([
            {"ability_id": r[0], "name": r[1], "skill_line_id": r[2], "skill_line_name": r[3] or ""}
            for r in rows
        ])
    finally:
        conn.close()


@app.route("/api/recommend")
def api_recommend():
    build_id = request.args.get("build_id", type=int)
    slot_id = request.args.get("slot_id", type=int)
    equipment = request.args.get("equipment")  # JSON array of {slot_id, game_id}
    if not build_id or not slot_id:
        return jsonify({"error": "build_id and slot_id required"}), 400
    equipment_list = []
    if equipment:
        try:
            raw = json.loads(equipment)
            for item in raw:
                sid = item.get("slot_id")
                gid = item.get("game_id")
                if sid is not None and gid is not None:
                    equipment_list.append((int(sid), int(gid)))
        except (json.JSONDecodeError, TypeError):
            pass
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        from recommendations import get_set_recommendations_for_slot
        recs = get_set_recommendations_for_slot(
            conn, build_id, slot_id,
            equipment=equipment_list or None,
        )
        return jsonify([dict(r) for r in recs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/weapon_glyphs")
def api_weapon_glyphs():
    build_id = request.args.get("build_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            "SELECT glyph_id, name, effect_text, effect_json FROM glyphs WHERE game_build_id = ? AND slot_kind = 'weapon' ORDER BY glyph_id",
            (build_id,),
        ).fetchall()
        return jsonify([
            {"glyph_id": r[0], "name": r[1], "effect_text": r[2], "effect_json": r[3]}
            for r in rows
        ])
    finally:
        conn.close()


@app.route("/api/weapon_poisons")
def api_weapon_poisons():
    build_id = request.args.get("build_id", type=int)
    if not build_id:
        return jsonify({"error": "build_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        rows = conn.execute(
            "SELECT poison_id, name, effect_text, duration_sec, effect_json FROM weapon_poisons WHERE game_build_id = ? ORDER BY poison_id",
            (build_id,),
        ).fetchall()
        return jsonify([
            {"poison_id": r[0], "name": r[1], "effect_text": r[2], "duration_sec": r[3], "effect_json": r[4]}
            for r in rows
        ])
    finally:
        conn.close()


@app.route("/api/enchant_poison_tradeoff")
def api_enchant_poison_tradeoff():
    """Compare impact of weapon enchant (glyph) vs weapon poison. Uses effect_json for magnitudes."""
    build_id = request.args.get("build_id", type=int)
    glyph_id = request.args.get("glyph_id", type=int)
    poison_id = request.args.get("poison_id", type=int)
    if not build_id or not glyph_id or not poison_id:
        return jsonify({"error": "build_id, glyph_id, and poison_id required"}), 400
    target_resistance = request.args.get("target_resistance", type=float, default=18200.0)
    hits_per_sec = request.args.get("hits_per_sec", type=float, default=1.0)
    base_dps = request.args.get("base_dps", type=float, default=0.0)
    poison_apps_per_sec = request.args.get("poison_applications_per_sec", type=float, default=0.5)
    penetration = request.args.get("penetration", type=float, default=6600.0)
    crit_chance = request.args.get("crit_chance", type=float, default=0.50)
    crit_damage = request.args.get("crit_damage", type=float, default=0.80)

    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 500
    try:
        g = conn.execute(
            "SELECT effect_json FROM glyphs WHERE game_build_id = ? AND glyph_id = ?",
            (build_id, glyph_id),
        ).fetchone()
        p = conn.execute(
            "SELECT duration_sec, effect_json FROM weapon_poisons WHERE game_build_id = ? AND poison_id = ?",
            (build_id, poison_id),
        ).fetchone()
    finally:
        conn.close()

    glyph_effect = g[0] if g else None
    poison_duration = p[0] if p else None
    poison_effect = p[1] if p else None

    from core.stat_block import StatBlock
    from core.weapon_enchant_tradeoff import compare_glyph_vs_poison

    stat = StatBlock(penetration=penetration, crit_chance=crit_chance, crit_damage=crit_damage)
    result = compare_glyph_vs_poison(
        glyph_effect,
        poison_effect,
        poison_duration,
        stat,
        target_resistance=target_resistance,
        hits_per_sec=hits_per_sec,
        poison_applications_per_sec=poison_apps_per_sec,
        base_dps=base_dps,
    )
    return jsonify({
        "glyph_impact": {
            "dps_contribution": result.glyph_impact.dps_contribution,
            "heal_per_sec": result.glyph_impact.heal_per_sec,
            "shield_per_sec": result.glyph_impact.shield_per_sec,
            "description": result.glyph_impact.description,
        },
        "poison_impact": {
            "dps_contribution": result.poison_impact.dps_contribution,
            "damage_taken_pct": result.poison_impact.damage_taken_pct,
            "description": result.poison_impact.description,
        },
        "recommendation": result.recommendation,
        "note": result.note,
    })


if __name__ == "__main__":
    # Use 0.0.0.0 so Expo Go on a phone (same LAN) can reach this server via your machine's IP.
    host = os.environ.get("ESO_BUILD_GENIUS_HOST", "127.0.0.1")
    app.run(host=host, port=5000, debug=True)
