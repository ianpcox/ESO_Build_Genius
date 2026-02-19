"""Integration tests for web API (Flask): build GET/POST, scribe_effects, catalog endpoints."""
from __future__ import annotations

import os
import pytest

# Ensure project root and scripts on path before importing app
from tests.conftest import PROJECT_ROOT
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from web.app import app


@pytest.fixture
def client(db_path):
    """Flask test client with test DB path."""
    prev = os.environ.get("ESO_BUILD_GENIUS_DB")
    os.environ["ESO_BUILD_GENIUS_DB"] = str(db_path)
    try:
        with app.test_client() as c:
            yield c
    finally:
        if prev is not None:
            os.environ["ESO_BUILD_GENIUS_DB"] = prev
        else:
            os.environ.pop("ESO_BUILD_GENIUS_DB", None)


@pytest.fixture
def game_build_id(conn):
    """ID of 'Update 48' game_build (used by API as default build_id)."""
    row = conn.execute("SELECT id FROM game_builds WHERE label = ?", ("Update 48",)).fetchone()
    return row[0] if row else 1


def test_api_build_get_no_param(client, game_build_id):
    """GET /api/build with no args returns build_id (game build)."""
    r = client.get("/api/build")
    assert r.status_code == 200
    data = r.get_json()
    assert "build_id" in data
    assert data["build_id"] == game_build_id


def test_api_build_get_with_recommended_build_id(client, conn, game_build_id):
    """GET /api/build?recommended_build_id=N returns build with equipment and bar_skills."""
    conn.execute(
        "INSERT OR IGNORE INTO skills (game_build_id, ability_id, name, mechanic) VALUES (?, 12345, 'TestSkill', 'Magicka')",
        (game_build_id,),
    )
    conn.execute(
        """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id)
           VALUES (?, 1, 1, 1, 11, 1, 1)""",
        (game_build_id,),
    )
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Use game_id that exists in set_summary for this game_build (seed has 2 and 3 for all builds)
    conn.execute(
        "INSERT INTO recommended_build_equipment (recommended_build_id, game_build_id, slot_id, game_id) VALUES (?, ?, 1, 2)",
        (bid, game_build_id),
    )
    conn.commit()
    conn.execute(
        """INSERT INTO recommended_build_scribed_skills (recommended_build_id, game_build_id, bar_slot_ord, ability_id, scribe_effect_id_1, scribe_effect_id_2, scribe_effect_id_3)
           VALUES (?, ?, 1, 12345, NULL, NULL, NULL)""",
        (bid, game_build_id),
    )
    conn.commit()
    conn.close()

    r = client.get("/api/build", query_string={"recommended_build_id": bid})
    assert r.status_code == 200
    data = r.get_json()
    assert data["recommended_build_id"] == bid
    assert data["build_id"] == game_build_id
    assert "equipment" in data
    assert data["equipment"] == [{"slot_id": 1, "game_id": 2}]
    assert "bar_skills" in data
    assert len(data["bar_skills"]) == 1
    assert data["bar_skills"][0]["bar_slot_ord"] == 1 and data["bar_skills"][0]["ability_id"] == 12345


def test_api_build_get_not_found(client, game_build_id):
    """GET /api/build?recommended_build_id=99999 returns 404."""
    r = client.get("/api/build", query_string={"recommended_build_id": 99999})
    assert r.status_code == 404


def test_api_build_post_create(client, game_build_id):
    """POST /api/build with required fields creates build and returns recommended_build_id."""
    payload = {
        "build_id": game_build_id,
        "class_id": 1,
        "race_id": 1,
        "role_id": 1,
        "mundus_id": 11,
        "food_id": 1,
        "potion_id": 1,
        "bar_skills": [{"bar_slot_ord": 1, "ability_id": 100}],
    }
    r = client.post("/api/build", json=payload, content_type="application/json")
    assert r.status_code == 200
    data = r.get_json()
    assert "recommended_build_id" in data
    assert isinstance(data["recommended_build_id"], int)


def test_api_build_post_update(client, conn, game_build_id):
    """POST /api/build with recommended_build_id updates bar_skills."""
    conn.execute(
        """INSERT INTO recommended_builds (game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id)
           VALUES (?, 1, 1, 1, 11, 1, 1)""",
        (game_build_id,),
    )
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    payload = {
        "build_id": game_build_id,
        "recommended_build_id": bid,
        "bar_skills": [
            {"bar_slot_ord": 1, "ability_id": 200, "scribe_effect_id_1": None, "scribe_effect_id_2": None, "scribe_effect_id_3": None},
            {"bar_slot_ord": 2, "ability_id": 201},
        ],
    }
    r = client.post("/api/build", json=payload, content_type="application/json")
    assert r.status_code == 200
    assert r.get_json()["recommended_build_id"] == bid

    r2 = client.get("/api/build", query_string={"recommended_build_id": bid})
    assert r2.status_code == 200
    bar = r2.get_json()["bar_skills"]
    assert len(bar) == 2
    assert bar[0]["ability_id"] == 200 and bar[1]["ability_id"] == 201


def test_api_build_post_missing_build_id(client):
    """POST /api/build without build_id returns 400."""
    r = client.post("/api/build", json={"bar_skills": []}, content_type="application/json")
    assert r.status_code == 400
    assert "build_id" in (r.get_json() or {}).get("error", "")


def test_api_build_post_bar_skills_required(client, game_build_id):
    """POST /api/build without bar_skills array returns 400."""
    r = client.post(
        "/api/build",
        json={"build_id": game_build_id, "class_id": 1, "race_id": 1, "role_id": 1, "mundus_id": 11, "food_id": 1, "potion_id": 1},
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "bar_skills" in (r.get_json() or {}).get("error", "")


def test_api_scribe_effects_build_id_required(client):
    """GET /api/scribe_effects without build_id returns 400."""
    r = client.get("/api/scribe_effects")
    assert r.status_code == 400
    assert "build_id" in (r.get_json() or {}).get("error", "")


def test_api_scribe_effects_returns_list(client, game_build_id):
    """GET /api/scribe_effects?build_id=N returns 200 and a list (may be empty)."""
    r = client.get("/api/scribe_effects", query_string={"build_id": game_build_id})
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_api_scribe_effects_with_ability_id(client, conn, game_build_id):
    """GET /api/scribe_effects?build_id=N&ability_id=M returns list (filtered when compat exists)."""
    r = client.get("/api/scribe_effects", query_string={"build_id": game_build_id, "ability_id": 12345})
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    # With no skill_scribe_compatibility rows, API returns full catalog for build; with compat, filtered. Either way list.


def test_api_catalog_classes(client):
    """GET /api/classes returns list of {id, name}."""
    r = client.get("/api/classes")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    for row in data[:3]:
        assert "id" in row and "name" in row


def test_api_catalog_slots(client):
    """GET /api/slots returns list."""
    r = client.get("/api/slots")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_api_index_serves_html(client):
    """GET / returns index.html."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.content_type
