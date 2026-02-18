# Database schema (SQLite)

All game data is versioned by `game_build_id`. One `game_builds` row per patch/snapshot (e.g. "Update 48 Incremental 3"); sets, skills, foods, etc. reference it.

## Core tables

| Table | Purpose |
|-------|--------|
| **game_builds** | Patch/snapshot id and label (e.g. api_version 101047). |
| **equipment_slots** | Fixed list: head, shoulders, chest, legs, feet, hands, waist, front_main, front_off, back_main, back_off. |
| **classes** | Dragonknight, Sorcerer, Nightblade, Templar, Warden, Necromancer, Arcanist. |
| **roles** | dd, healer, tank, support_dd. |
| **ingest_runs** | Optional provenance: which addon/UESP run filled this build. |

## Versioned game data (per build)

| Table | Key columns | Notes |
|-------|-------------|--------|
| **races** | id, name | Names only; effects in race_effects. |
| **race_effects** | game_build_id, race_id, effect_text, magnitude | Passives per build. |
| **item_sets** | game_build_id, set_id, name, set_type, max_pieces | set_type: crafted, dungeon, trial, monster, mythic, etc. |
| **set_bonuses** | game_build_id, set_id, num_pieces, effect_text | One row per (2pc, 3pc, 4pc, 5pc) or (1pc mythic / 2pc monster). |
| **set_slots** | game_build_id, set_id, slot_id | Which slots this set can occupy. |
| **skills** | game_build_id, ability_id, name, skill_line, class_name, mechanic, coefficient_json | coefficient_json for damage formula. |
| **buffs** | game_build_id, buff_id, name, effect_type, magnitude | Major/Minor buffs and debuffs. |
| **mundus_stones** | game_build_id, mundus_id, name, effect_text, magnitude | One per character. |
| **foods** | game_build_id, food_id, name, duration_sec, effect_json | effect_json: max stats, recovery. |
| **potions** | game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_json | Buffs and resource restore. |

## Optimizer output

| Table | Purpose |
|-------|--------|
| **recommended_builds** | One row per (game_build_id, class_id, role_id): race, mundus, food, potion, score_dps. |
| **recommended_build_equipment** | (recommended_build_id, slot_id, set_id): which set is in which slot. |

## Optional (later)

| Table | Purpose |
|-------|--------|
| **trials** | Trial names. |
| **trial_bosses** | Bosses per trial for per-boss overrides. |

## Creating the DB

From project root:

```bash
python scripts/create_db.py
```

Default path: `data/eso_build_genius.db`. Override with:

```bash
python scripts/create_db.py path/to/custom.db
```

## Reference data (seeded in 01_schema.sql)

- **set_types:** crafted, dungeon, trial, overland, arena, monster, mythic, pvp  
- **equipment_slots:** 11 slots (7 body + 4 weapon)  
- **classes:** 7 ESO classes  
- **roles:** dd, healer, tank, support_dd  
- **races:** 10 playable races (effects loaded per build)
