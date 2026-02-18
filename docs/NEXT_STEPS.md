# What's next – ESO Build Genius

Prioritised list of next work. Schema and design are in place; data and optimisation logic are the main gaps. **UI design** is captured in [UI_DESIGN.md](UI_DESIGN.md) (form, 14-slot equipment layout, Advisor, 12-skill bar).

## 1. Data: seed and ingest

| Priority | Task | Notes |
|----------|------|--------|
| **Done** | Class skill lines | 21 lines (3 per class) seeded in `07_seed_skill_lines_and_buffs.sql`. |
| **Done** | Minimal buffs + example set link | Buff catalog and `buff_grants_set_bonus` example in 07. |
| **Done** | Link skills to skill lines | `09_skill_lines_weapon_guild.sql` adds weapon/guild/world lines (801-810). `scripts/link_skills_to_skill_lines.py` parses class sheets from the Damage Skills xlsx and sets `skills.skill_line_id` and `skills.skill_line`. Run after ingest. |
| **Done** | Populate buff_grants (abilities) | `scripts/populate_buff_grants.py`: curated mapping (skill name → buff_id) + optional `--parse-description` to link from skills.description keywords. Run after ingest; adds ability→buff rows for duplicate-buff logic. |
| Next | Item sets + set bonuses | Ingest from addon export or ESO Sets API so set recommendations and `buff_grants_set_bonus` have real sets. |
| Later | Weapon Comparisons → weapon_type_stats | From Standalone Calculator xlsx. |
| Later | Harpooner's Wading Kilt → trial_boss_set_notes | Needs trials/bosses and set IDs. |
| Later | Scribe effects catalog | Populate `scribe_effects` when source (e.g. addon or UESP) is available. |

## 2. Optimisation logic

| Priority | Task | Notes |
|----------|------|--------|
| **Done** | Buff coverage helper | `scripts/buff_coverage.py`: get_buff_coverage(ability_ids, set_pieces, skill_line_ids). |
| **Done** | Duplicate-buff filter in recommendations | `scripts/recommendations.py` + `scripts/recommend_sets.py`: set suggestions per slot; flag sets that only duplicate self-buff coverage. **Self-buffs only** (abilities + passives + equipped sets); team composition / external buffs later. |
| **Done** | Set recommendations (Advisor-style) | Use `recommend_sets.py --build-id N --slot SLOT [--abilities ...] [--equipment "slot_id,set_id" ...]` to list candidate sets and redundancy. |
| Later | Stat block / damage formula | Use `stat_modifier_reference`, penetration, crit, etc. from Standalone Calculator. |
| Later | Subclassing constraint | When building recommended_build_class_lines, enforce “at most 2 of 3 lines from other classes”. |
| Later | Full optimizer | Combinatoric search over sets, mundus, food, potions, subclass lines, scribed variants; integrate buff coverage and duplicate avoidance. |

## 3. Pipeline and tooling

| Priority | Task | Notes |
|----------|------|--------|
| Later | Addon export → item_sets / skills | Parse addon JSON or Lua into DB (sets, skills, maybe buffs). |
| Later | ESO API version check | Use esoapi.uesp.net or esodata.uesp.net to detect new build and trigger re-ingest. |
| Later | Patch notes labelling | Map build id to "Update XX" for display. |

## 4. Suggested order to tackle next

1. Run `create_db` and `ingest_xlsx --build-label "Update 39"` so DB has game_build, skills, stat_modifier_reference.
2. Run seed (07) so skill_lines and buffs exist for game_build_id 1 (or ensure Default build exists).
3. **Buff coverage and recommendations** are implemented: `buff_coverage.py` and `recommendations.py` / `recommend_sets.py`. Recommendations use **self-buff coverage only** (no team buffs yet); a **team composition optimizer** (who provides which buffs) is planned after the individual build optimizer is in place.
4. Add more `buff_grants_set_bonus` rows (e.g. from set bonus text or addon) so redundancy flags are meaningful for more sets.
