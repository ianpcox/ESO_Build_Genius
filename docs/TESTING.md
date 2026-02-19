# Testing – ESO Build Genius

## Quick start

```bash
pip install -r requirements-test.txt
pytest
```

With coverage:

```bash
pytest --cov=core --cov-report=term-missing
pytest --cov=core --cov-report=html
```

## Layout

- **tests/unit/** – Unit tests for `core` and for `scripts/buff_coverage`, `scripts/recommendations`. Use a session-scoped in-memory DB built from `schema/*.sql` (see `tests/conftest.py`).
- **tests/integration/** – Flows that span multiple modules: stat block → damage, rotation DPS → fight duration, optimizer-style write + `ensure_build_class_lines` + `validate_subclass_lines`; **test_api.py** – Web API (Flask): GET/POST `/api/build`, `/api/scribe_effects` (with optional `ability_id`), catalog endpoints, index.

## Fixtures

- **db_path** (session) – Path to a temporary DB with full schema applied.
- **conn** – Open connection to that DB (closed after each test).
- **game_build_id** – Default `1` (from seed).

## Running subsets

```bash
pytest tests/unit/test_damage.py -v
pytest tests/unit/test_subclassing.py -v
pytest tests/integration/ -v
pytest tests/integration/test_api.py -v
pytest -k "weapon" -v
```

## Smoke tests (no pytest)

End-to-end smoke tests using the real DB in `data/`:

```bash
python scripts/run_app_tests.py
python scripts/run_app_tests.py --no-create
```

These run create_db, stat_block_damage_demo, weapon_comparison_demo, run_optimizer (dry-run and write), recommend_sets, buff_coverage, and subclassing validation.
