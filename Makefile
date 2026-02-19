# ESO Build Genius – pipeline and tooling
# Run from project root. If make is not available (e.g. Windows), use:
#   python scripts/run_pipeline.py --build-label "Update 48" --replace
#   python scripts/run_app_tests.py
#   python web/app.py

PY     := python
DB     := data/eso_build_genius.db
LABEL  := Update 48
REPLACE :=

.PHONY: db fetch ingest-sets ingest-buff-grants ingest-skills link-skills ingest-food-potions pipeline pipeline-py test test-no-create web help

help:
	@echo "Targets:"
	@echo "  make db              - Create/reset DB from schema"
	@echo "  make fetch           - Fetch foods.json and potions.json from UESP"
	@echo "  make ingest-sets     - Ingest sets (UESP) into DB"
	@echo "  make ingest-buff-grants - Populate buff_grants_set_bonus"
	@echo "  make ingest-skills   - Ingest skills/coefficients (UESP)"
	@echo "  make link-skills     - Link skills to skill lines (xlsx)"
	@echo "  make ingest-food-potions - Ingest foods + potions from data/*.json"
	@echo "  make pipeline        - Full pipeline (db + fetch + all ingests + link-skills)"
	@echo "  make pipeline-py     - Same via scripts/run_pipeline.py (supports --replace, --skip-*)"
	@echo "  make test            - Smoke tests (create_db + demos + optimizer + recommend_sets)"
	@echo "  make test-no-create  - Smoke tests using existing DB"
	@echo "  make web             - Start Flask app on port 5000"
	@echo ""
	@echo "Override: make pipeline DB=data/eso_build_genius.db LABEL=\"Update 48\" REPLACE=--replace"

db:
	$(PY) scripts/create_db.py $(DB)

fetch:
	$(PY) scripts/fetch_foods_uesp.py --out data/foods.json
	$(PY) scripts/fetch_potions_uesp.py --out data/potions.json

ingest-sets:
	$(PY) scripts/ingest_sets_uesp.py --db $(DB) --build-label "$(LABEL)" $(REPLACE)

ingest-buff-grants:
	$(PY) scripts/populate_buff_grants_set_bonus.py --db $(DB) --build-label "$(LABEL)" $(REPLACE)

ingest-skills:
	$(PY) scripts/ingest_skills_uesp.py --db $(DB) --build-label "$(LABEL)" $(REPLACE)

link-skills:
	$(PY) scripts/link_skills_to_skill_lines.py --db $(DB)

ingest-food-potions:
	$(PY) scripts/ingest_food_potions.py --db $(DB) --build-label "$(LABEL)" --foods-json data/foods.json --potions-json data/potions.json $(REPLACE)

pipeline: db fetch ingest-sets ingest-buff-grants ingest-skills link-skills
	@if [ -f data/foods.json ] || [ -f data/potions.json ]; then $(MAKE) ingest-food-potions DB=$(DB) LABEL="$(LABEL)" REPLACE="$(REPLACE)"; fi
	@echo "Pipeline done. Optional: make ingest-food-potions (if fetch wrote JSON), make test, make web"

pipeline-py:
	$(PY) scripts/run_pipeline.py --db $(DB) --build-label "$(LABEL)" $(REPLACE)

test:
	$(PY) scripts/run_app_tests.py --db $(DB)

test-no-create:
	$(PY) scripts/run_app_tests.py --db $(DB) --no-create

web:
	$(PY) web/app.py
