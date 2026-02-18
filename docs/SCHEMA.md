# Database schema (SQLite)

The schema is **component-first**: each component (race, class, equipment set, skill, buff, mundus, food, potion) has its own table(s) with a single responsibility. Builds are **composition only** (references to component IDs). See [SCHEMA_OVERVIEW.md](SCHEMA_OVERVIEW.md) for the design principle.

## Quick reference by component

| Component | Table(s) | Versioned? |
|-----------|----------|------------|
| Versioning | `game_builds` | - |
| Lookups | `equipment_slots`, `set_types`, `classes`, `roles` | No |
| Race | `races`, `race_effects` | race_effects per build |
| Equipment set | `item_sets`, `set_bonuses`, `set_slots` | Yes |
| Skill | `skills` | Yes |
| Buff | `buffs` | Yes |
| Mundus | `mundus_stones` | Yes |
| Food | `foods` | Yes |
| Potion | `potions` | Yes |
| Ingest | `ingest_runs` | - |
| Trial | `trials`, `trial_bosses` (+ `trial_boss_set_notes` in 03) | No / per build for notes |
| **Build (composition)** | `recommended_builds`, `recommended_build_equipment` | References components only |

## Key columns (for joins)

- **item_sets:** (game_build_id, set_id), name, set_type, max_pieces  
- **set_bonuses:** (game_build_id, set_id, num_pieces), effect_text, effect_type, magnitude  
- **set_slots:** (game_build_id, set_id, slot_id)  
- **skills:** (game_build_id, ability_id), name, skill_line, class_name, base_tooltip, adps, cost, duration_sec, cast_time_sec, coefficient_json, ...  
- **recommended_builds:** game_build_id, class_id, role_id, race_id, mundus_id, food_id, potion_id, score_dps, weapon_type, simulation_target_id  
- **recommended_build_equipment:** recommended_build_id, slot_id, set_id, game_build_id  

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
