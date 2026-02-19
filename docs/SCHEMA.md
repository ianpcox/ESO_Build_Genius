# Database schema (SQLite)

The schema is **component-first**: each component (race, class, equipment set, skill, buff, mundus, food, potion) has its own table(s) with a single responsibility. Builds are **composition only** (references to component IDs). See [SCHEMA_OVERVIEW.md](SCHEMA_OVERVIEW.md) for the design principle.

## Quick reference by component

| Component | Table(s) | Versioned? |
|-----------|----------|------------|
| Versioning | `game_builds` | - |
| Lookups | `equipment_slots`, `set_types`, `classes`, `roles` | No |
| Race | `races`, `race_effects` | race_effects per build |
| Equipment set | `set_summary`, `set_bonuses`, `set_item_slots` (UESP-aligned) | Yes |
| Skill | `skills` | Yes |
| Skill line | `skill_line_types`, `skill_lines`, `skill_line_passives` (04) | Yes |
| Buff | `buffs` | Yes |
| Buff grants | `buff_grants` (04), `buff_grants_set_bonus` (06) | Yes |
| Target type | `target_types`, `skill_target_bonus` (04) | target_types no; skill_target_bonus yes |
| Scribing | `scribe_effect_slots`, `scribe_effects`, `skill_scribe_compatibility`, `recommended_build_scribed_skills` (05) | scribe_effect_slots no; rest yes |
| Mundus | `mundus_stones` | Yes |
| Food | `foods` | Yes |
| Potion | `potions` | Yes |
| Ingest | `ingest_runs` | - |
| Trial | `trials`, `trial_bosses` (+ `trial_boss_set_notes` in 03) | No / per build for notes |
| **Build (composition)** | `recommended_builds`, `recommended_build_equipment`, `recommended_build_class_lines` (04), `recommended_build_scribed_skills` (05) | References components only; class_lines = subclassing; scribed_skills = bar layout with base + 0–3 scribe effects per slot |

## Key columns (for joins)

- **set_summary:** (game_build_id, game_id), set_name, type, set_max_equip_count (UESP setSummary)  
- **set_bonuses:** (game_build_id, game_id, num_pieces), set_bonus_desc, effect_type, magnitude  
- **set_item_slots:** (game_build_id, game_id, slot_id) (UESP itemSlots normalized)  
- **skills:** (game_build_id, ability_id), name, skill_line, class_name, base_tooltip, adps, cost, duration_sec, cast_time_sec, coefficient_json, ...  
- **recommended_builds:** game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, weapon_type, simulation_target_id  
- **recommended_build_equipment:** recommended_build_id, slot_id, game_id, game_build_id  
- **skill_lines (04):** (game_build_id, skill_line_id), name, skill_line_type, class_id (for class lines)  
- **skill_line_passives (04):** (game_build_id, skill_line_id, passive_ord), name, effect_text  
- **buff_grants (04):** (game_build_id, buff_id), grant_type ('ability'|'passive'), ability_id or (skill_line_id, passive_ord)  
- **buff_grants_set_bonus (06):** (game_build_id, buff_id, game_id, num_pieces) – which set bonus grants which buff (for duplicate-buff avoidance)  
- **target_types (04):** id, name (Any, Undead, Daedra, Humanoid, Beast, Construct, Player)  
- **skill_target_bonus (04):** (game_build_id, ability_id, target_type_id), effect_text, magnitude  
- **recommended_build_class_lines (04):** recommended_build_id, slot_ord (1..3), skill_line_id, game_build_id  
- **scribe_effect_slots (05):** id, name (Focus, Signature, Affix)  
- **scribe_effects (05):** (game_build_id, scribe_effect_id), name, slot_id, effect_text, effect_type, magnitude, resource_type  
- **skill_scribe_compatibility (05):** (game_build_id, ability_id, scribe_effect_id) – which effects can apply to which base skills  
- **recommended_build_scribed_skills (05):** recommended_build_id, bar_slot_ord, ability_id, scribe_effect_id_1, scribe_effect_id_2, scribe_effect_id_3 (nullable), game_build_id  

## Creating the DB

From project root:

```bash
python scripts/create_db.py
```

Default path: `data/eso_build_genius.db`. Override with:

```bash
python scripts/create_db.py path/to/custom.db
```

## Seed data (in 01_schema.sql)

- **set_types:** crafted, dungeon, trial, overland, arena, monster, mythic, pvp  
- **equipment_slots:** 11 slots (7 body + 4 weapon)  
- **classes:** 7 ESO classes  
- **roles:** dd, healer, tank, support_dd  
- **races:** 10 playable races (effects loaded per build into race_effects)
