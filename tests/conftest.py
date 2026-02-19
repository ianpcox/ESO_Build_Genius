"""
Pytest fixtures: minimal DB built from schema for tests.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

# Project root (parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# Scripts for buff_coverage, recommendations
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SCHEMA_DIR = PROJECT_ROOT / "schema"


def _build_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    for path in sorted(SCHEMA_DIR.glob("*.sql")):
        conn.executescript(path.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


@pytest.fixture(scope="session")
def db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped path to a test DB with full schema (no ingest data)."""
    path = tmp_path_factory.mktemp("db") / "eso_build_genius.db"
    _build_db(path)
    return path


@pytest.fixture
def conn(db_path: Path) -> sqlite3.Connection:
    """Connection to the test DB. Closed after test."""
    c = sqlite3.connect(str(db_path))
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


@pytest.fixture(scope="session")
def game_build_id() -> int:
    """Default game_build id (1) from schema seed."""
    return 1
