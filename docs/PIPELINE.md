# Pipeline and tooling – ESO Build Genius

This doc describes the **data pipeline** (create DB, fetch, ingest, link) and **tooling** (Makefile, smoke tests, web app). Target patch: **Patch 48** (Update 48). See [CURRENT_PATCH.md](CURRENT_PATCH.md) and [DATA_SOURCES.md](DATA_SOURCES.md).

## Pipeline order

Steps run in this order. Later steps depend on earlier ones.

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `create_db.py` | Create or reset SQLite DB from `schema/*.sql` |
| 2 | `fetch_foods_uesp.py` | Write `data/foods.json` from UESP wiki |
| 3 | `fetch_potions_uesp.py` | Write `data/potions.json` from UESP wiki |
| 4 | `ingest_sets_uesp.py` | Sets from UESP ESO Log setSummary → set_summary, set_bonuses, set_item_slots |
| 5 | `populate_buff_grants_set_bonus.py` | Parse set bonus text → buff_grants_set_bonus |
| 6 | `ingest_skills_uesp.py` | Skills + coefficients from UESP skillCoef → skills.coefficient_json |
| 7 | `link_skills_to_skill_lines.py` | Map skills to skill_lines using Damage Skills xlsx |
| 8 | `ingest_food_potions.py` | foods.json + potions.json → foods, potions tables |
| 9 (optional) | `ingest_xlsx.py` | Damage Skills xlsx + stat ref + weapon comparisons |
| 10 (optional) | `verify_skill_lines_esolog.py` | Compare class skill lines to ESO Log |
| 11 (optional) | `link_skill_lines_from_esolog.py` | Set skills.skill_line_id from ESO Log playerSkills |

## Running the pipeline

### Option A: Single script (recommended)

```bash
python scripts/run_pipeline.py --build-label "Update 48" --replace
```

- **Without --replace:** New data is added; existing rows may be left as-is (script-dependent).
- **Skip steps:** `--skip-db`, `--skip-fetch`, `--skip-sets`, `--skip-buff-grants`, `--skip-skills`, `--skip-link-skills`, `--skip-food-potions`.
- **Optional steps:** `--run-xlsx`, `--verify-esolog`, `--link-esolog`.
- **Dry run:** `--dry-run` (skips DB writes where supported; fetches still run).
- **DB path:** `--db data/eso_build_genius.db` (default).

Example: sets and buff grants only (no skills, no fetch):

```bash
python scripts/run_pipeline.py --build-label "Update 48" --replace --skip-fetch --skip-skills --skip-link-skills --skip-food-potions
```

### Option B: Makefile

From project root (requires `make`; on Windows you can use Git Bash or run Option A):

```bash
make help
make db
make fetch
make pipeline
make pipeline REPLACE=--replace
make pipeline-py
make pipeline-py REPLACE=--replace
```

Variables: `DB=data/eso_build_genius.db`, `LABEL="Update 48"`, `REPLACE=--replace`.

- **make pipeline** – Runs db, fetch, ingest-sets, ingest-buff-grants, ingest-skills, link-skills; then ingest-food-potions if `data/foods.json` or `data/potions.json` exists.
- **make pipeline-py** – Runs `scripts/run_pipeline.py` with the same DB/LABEL/REPLACE (so you get --replace and optional steps via the script if you run it manually with extra args).

### Option C: Individual scripts

See [DATA_SOURCES.md](DATA_SOURCES.md) for suggested ingestion order and script usage. Example:

```bash
python scripts/create_db.py
python scripts/fetch_foods_uesp.py
python scripts/fetch_potions_uesp.py
python scripts/ingest_sets_uesp.py --build-label "Update 48" --replace
python scripts/populate_buff_grants_set_bonus.py --build-label "Update 48" --replace
python scripts/ingest_skills_uesp.py --build-label "Update 48" --replace
python scripts/link_skills_to_skill_lines.py
python scripts/ingest_food_potions.py --build-label "Update 48" --foods-json data/foods.json --potions-json data/potions.json --replace
```

## Tooling

| Task | Command |
|------|--------|
| **Unit + integration tests** | `pytest` or `pytest --cov=core` (see [TESTING.md](TESTING.md)) |
| **Smoke tests** | `python scripts/run_app_tests.py` (create_db, demos, optimizer, recommend_sets, buff_coverage, subclassing) |
| **Smoke tests (existing DB)** | `python scripts/run_app_tests.py --no-create` |
| **Start web UI** | `python web/app.py` → http://127.0.0.1:5000/ |
| **Makefile smoke** | `make test` or `make test-no-create` |
| **Makefile web** | `make web` |

## Dependencies

- **Pipeline:** Python 3, `requests` (or urllib) for UESP fetches; `pandas`, `openpyxl` for `link_skills_to_skill_lines` and `ingest_xlsx`.
- **Tests:** `pytest`, optional `pytest-cov`; see `requirements-test.txt`.
- **Web:** Flask; see `requirements.txt`.

Install:

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## What’s not in the pipeline (yet)

- **Addon export** – No script to import addon JSON/Lua into set_summary/skills.
- **ESO API version check** – No automatic detection of new game build to trigger re-ingest.
- **Patch notes labelling** – Build labels are manual (e.g. "Update 48"); see [PATCH_SOURCES.md](PATCH_SOURCES.md).

These are noted in [NEXT_STEPS.md](NEXT_STEPS.md) § Pipeline and tooling.
