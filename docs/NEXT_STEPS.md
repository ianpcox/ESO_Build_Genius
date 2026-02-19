# What's next – ESO Build Genius

Prioritised list of next work. Schema and design are in place; **data** and **optimisation logic** are the main gaps. **UI design** is in [UI_DESIGN.md](UI_DESIGN.md) (form, 14-slot equipment, Advisor, 12-skill bar). This is a complex project; the roadmap below reflects [DESIGN_PLAN.md](DESIGN_PLAN.md) phases 1–6.

## Where we are (short)

| Layer | Status |
|-------|--------|
| **Schema** | Done: versioned components (set_summary, set_bonuses, set_item_slots, skills, buffs, skill_lines, scribing, trials, etc.) and build composition tables. |
| **Seed / lookups** | Done: game_builds, set_types, equipment_slots (14), classes, roles, races, skill_lines (class + weapon/guild), skill_line_types, target_types, scribe_effect_slots; buffs 1–43 (07 + 07b); one example set (Kinras) + buff_grants_set_bonus at scale via populate_buff_grants_set_bonus.py. |
| **Set data** | Done: UESP ingest (`ingest_sets_uesp.py`) → set_summary, set_bonuses, set_item_slots (~706 sets). |
| **Skill data** | Done: xlsx ingest (Damage Skills) + **UESP skillCoef ingest** (`ingest_skills_uesp.py`) → skills with `coefficient_json` (type, a, b, c, R, avg) for damage/heal formulae. link_skills_to_skill_lines; populate_buff_grants. |
| **Buff coverage & set recommendations** | Done: self-buff coverage, recommend_sets.py per slot with redundancy flags. Team composition later. |
| **Stat block / damage formula** | Started: `core/stat_block.py` and `core/damage.py`. Stat block from race_effects, mundus, set_bonuses, food/potion (effect_json). Damage = base from coefficient_json then crit, damage_done_pct, armor mitigation. Demo: `scripts/stat_block_damage_demo.py`. |
| **Optimizer** | Started: slot rules in `core/slot_rules.py` (5+5+2); `scripts/run_optimizer.py` enumerates combos, scores by stat proxy, writes top builds to recommended_builds/equipment. Full DPS scoring and mythic option next. |
| **Other roles** | Not started: healer, tank, support DD (separate objectives: HPS, survivability, taunt/buff/debuff uptime). |
| **Trials / bosses** | Schema only; trials, trial_bosses, trial_boss_set_notes empty. Kilt-style notes and per-boss tuning later. |
| **UI** | Design only; no app yet. |

## 1. Data: seed and ingest

| Priority | Task | Notes |
|----------|------|--------|
| **Done** | Class skill lines | 21 lines (3 per class) in 07. |
| **Done** | Minimal buffs + example set link | 07: buffs 1–6, Kinras 5pc → Major Berserk, buff_grants_set_bonus. |
| **Done** | Link skills to skill lines | 09 weapon/guild lines; `link_skills_to_skill_lines.py` from xlsx. |
| **Done** | Populate buff_grants (abilities) | `populate_buff_grants.py` for ability→buff. |
| **Done** | Item sets (UESP) | `ingest_sets_uesp.py` → set_summary, set_bonuses, set_item_slots. |
| **Done** | Mundus, food, potions | Seed in 10_seed_mundus_food_potions.sql; full foods via fetch_foods_uesp.py + ingest_food_potions.py. |
| **Done** | Race effects | `schema/13_seed_race_effects.sql` seeds race_effects from UESP wiki race pages (4 passives per race, max-rank text). Run create_db or execute seed; needed for stat block. |
| **Done** | Skill coefficients | `ingest_skills_uesp.py` fetches esolog skillCoef; stores in skills.coefficient_json for damage formula. |
| **Done** | buff_grants_set_bonus at scale | **Source:** set_bonuses.set_bonus_desc (from UESP setSummary). **Pipeline:** Run `create_db.py` (includes 07b buffs), then `ingest_sets_uesp.py`, then `populate_buff_grants_set_bonus.py --build-label "Update 48" [--replace]`. Parses bonus text for Major/Minor buff names; comprehensive store for every set in the game. Ingest is aligned to **Patch 48**; see [CURRENT_PATCH.md](CURRENT_PATCH.md) and [DATA_SOURCES.md](DATA_SOURCES.md). |
| **Done** | Weapon type stats and comparisons | `weapon_type_stats` seeded from Twin Blade and Blunt (Dual Wield); `core/weapon_type.py` applies bonuses with dual-wield halved rule. **ingest_xlsx** can ingest **Weapon Comparisons** sheet from Standalone Calculator xlsx for other weapon lines (2H, Bow, Staff). |
| **Later** | trial_boss_set_notes | Trials/bosses + set IDs; e.g. Kilt cheat sheet. |
| **Later** | Trial boss + trash pack data | **Standalone data source** for per-boss (resistance, HP, mechanics) and per-pack (composition, enemy types). See DATA_SOURCES.md § Trial boss and trash pack data. |
| **Later** | Scribe effects catalog | scribe_effects, skill_scribe_compatibility when source available. |

## 2. Optimisation logic

| Priority | Task | Notes |
|----------|------|--------|
| **Done** | Buff coverage helper | `scripts/buff_coverage.py`: get_buff_coverage(ability_ids, set_pieces, skill_line_ids). |
| **Done** | Duplicate-buff filter in recommendations | `scripts/recommendations.py` + `scripts/recommend_sets.py`: set suggestions per slot; flag sets that only duplicate self-buff coverage. **Self-buffs only** (abilities + passives + equipped sets); team composition / external buffs later. |
| **Done** | Set recommendations (Advisor-style) | Use `recommend_sets.py --build-id N --slot SLOT [--abilities ...] [--equipment "slot_id,game_id" ...]` to list candidate sets and redundancy. |
| **Done** | Stat block / damage formula | stat_block uses race_effects, mundus, set_bonuses, weapon_type_stats, food/potion effect_json. **stat_modifier_reference** (References for Stats) ingested via ingest_xlsx; `core/stat_reference.py` and stat block apply reference caps when populated. |
| Later | Subclassing constraint | When building recommended_build_class_lines, enforce “at most 2 of 3 lines from other classes”. |
| Later | Full optimizer | Combinatoric search over sets, mundus, food, potions, subclass lines, scribed variants; integrate buff coverage and duplicate avoidance. |
| Later | Optimal ultimate usage | Two ultimates: one usually passive/self-buff, debuff, or group buff (often front bar); one damage (often back bar). Score bar assignment and tradeoff when debuff/group-buff is on back bar (swap cost vs damage-ultimate availability). See COMBAT_TIMING_AND_SIMULATION.md §9. |

## 3. Pipeline and tooling

| Priority | Task | Notes |
|----------|------|--------|
| **Done** | Test coverage | **pytest:** `tests/unit/`, `tests/integration/`. Run `pytest` or `pytest --cov=core`. See [TESTING.md](TESTING.md). Smoke: `python scripts/run_app_tests.py`. |
| **Done** | Pipeline runner and Makefile | **run_pipeline.py:** single entry point for create_db → fetch → ingest sets/buff_grants/skills → link_skills → ingest_food_potions; optional --run-xlsx, --verify-esolog, --link-esolog. **Makefile:** db, fetch, ingest-*, pipeline, pipeline-py, test, web. See [PIPELINE.md](PIPELINE.md). |
| Later | Addon export → set_summary / skills | Parse addon JSON or Lua into DB (sets, skills, maybe buffs). |
| Later | ESO API version check | Use esoapi.uesp.net or esodata.uesp.net to detect new build and trigger re-ingest. |
| Later | Patch notes labelling | Map build id to "Update XX" for display. Ingest and build labels are aligned to **Patch 48**; see [CURRENT_PATCH.md](CURRENT_PATCH.md). |

## 4. Logical next steps (suggested order)

**Next (core loop: stat block to damage to optimizer):**

1. **Stat block calculator** – Done in core/stat_block.py: compute_stat_block() returns StatBlock from race_effects, mundus, set_bonuses, food/potion. Demo: scripts/stat_block_damage_demo.py.
2. **Single-target damage estimate** – Done in core/damage.py: damage_per_hit(stat_block, coefficient_json, use_stamina, target_resistance=...) returns expected damage per hit (or tick).
3. **Damage formula (full)** – Done in core/damage.py: same function applies crit, damage_done_pct, armor mitigation, target damage-taken (e.g. Major Vuln).
4. **Slot rules and first optimizer** – Done: `core/slot_rules.py` enforces 5+5+2 and 5+4+2+1 (mythic). `scripts/run_optimizer.py` enumerates combos; scores by stat proxy or **rotation DPS** via `core.rotation.rotation_dps` with `--ability-ids` and optional `--rotation-weights` (hits/sec per ability); writes top N to recommended_builds/equipment. Next: full time-step simulator (DoT tick timing, LA weave).

**Next (scenarios: per-trial, per-boss, and trash vs boss):**

Builds are **dependent on a per-trial, per-boss basis**; optimisation is not only single-target boss damage but also **AOE for trash packs** between bosses (see COMBAT_TIMING_AND_SIMULATION.md §10).

5. **Simulation scenarios** – Done: `simulation_targets` has **encounter_type** ('single_target' | 'aoe') and **hp** (optional). Seed: vet_dungeon_boss, trial_dummy_21m (21M HP), trial_trash_generic (aoe). For existing DBs run `python scripts/migrate_simulation_targets_scenarios.py`. Next: use when scoring (best for vCR Olms vs vCR trash vs 21M parse); optional buff/debuff assumptions per scenario.
6. **Trials and bosses (and trash)** – Done: **trials** and **trial_bosses** populated (seed 16: 14 trials, 42 bosses). **trial_trash_packs** and **trial_trash_pack_enemies** added (schema 18) with one placeholder pack per trial; pack composition to be filled from standalone source. Add trial_boss_set_notes (e.g. Kilt cheat sheet) and link bosses/trash to scenario profiles. Per-boss stats (resistance, HP) and full trash composition still require standalone data source (DATA_SOURCES.md).
7. **Subclassing** – `core/subclassing.py`: `validate_subclass_lines(conn, recommended_build_id)` enforces at most 2 of 3 class-line slots from other classes. `get_default_class_lines_for_class` / `ensure_build_class_lines` default new builds to the base class's 3 lines; **run_optimizer** calls `ensure_build_class_lines` so recommended builds get class lines. ESO Log **playerSkills** (classType, skillLine) used to verify seed and optionally link `skills.skill_line_id` via `scripts/verify_skill_lines_esolog.py` and `scripts/link_skill_lines_from_esolog.py`.
8. **Weapon and stat reference** – Done: weapon_type_stats seeded (Dual Wield) in schema 14; **ingest_xlsx** ingests **References for Stats** -> stat_modifier_reference and **Weapon Comparisons** -> weapon_type_stats from Standalone Damage Modifiers Calculator xlsx. `core/stat_reference.py` exposes reference by category; stat block applies reference caps when populated. Use `ingest_xlsx.py` with the Calculator xlsx in data/ for full coverage; skip weapon comparisons with `--skip-weapon-comparisons` if sheet layout differs.

**Later (expansion):**

9. **Healer, tank, support DD** – Separate objectives: healers (HPS plus buff and debuff uptime), tanks (survivability, taunt uptime, plus buff and debuff uptime), support DD (utility); different set filters and scoring.
10. **UI** – Build form, 14-slot equipment, Advisor (recommend_sets + buff coverage), 12-skill bar (see UI_DESIGN.md).
11. **Team composition** – Who provides which buffs (healer/tank); avoid duplicate buffs across the group.
12. **Scribing** – scribe_effects catalog and recommended_build_scribed_skills when source is available.
13. **Pipeline and tooling** – Done: run_pipeline.py + Makefile (see PIPELINE.md). Later: addon export to DB; ESO API version check for new builds; patch-notes labelling for build display.
