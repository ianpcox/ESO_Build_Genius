# Schema overview: components first, build = composition

The database is organized so that **components** (race, class, equipment set, skill, buff, mundus, food, potion) each have their own tables with a single responsibility. **Builds** are only a composition of references to those components; they do not store component data.

## Principle

- **Component table** = one kind of thing, one job. e.g. `races` + `race_effects` = "what races exist and what passives they have."
- **Build table** = which components are combined (e.g. this build uses race_id 7, these sets in these slots, this mundus, this food, this potion). All real data lives in the component tables.

## Component responsibilities

| Component | Table(s) | Responsibility |
|-----------|----------|----------------|
| **Versioning** | `game_builds` | Which game patch/snapshot this data is for. |
| **Lookups** | `equipment_slots`, `set_types`, `classes`, `roles` | Fixed reference lists (slots, set type, class, role). |
| **Race** | `races`, `race_effects` | Races and their passives (per build). |
| **Equipment set** | `item_sets`, `set_bonuses`, `set_slots` | Sets, piece bonuses, and which slots a set can occupy. |
| **Skill** | `skills` | Skills/abilities and coefficients, tooltips, cost, duration. |
| **Buff** | `buffs` | Buffs/debuffs (name, effect type, magnitude). |
| **Mundus** | `mundus_stones` | Mundus stones and their effects. |
| **Food** | `foods` | Food/drink and stat effects. |
| **Potion** | `potions` | Potions and effects/cooldowns. |
| **Simulation target** | `simulation_targets` (in 03) | Target resistance/pen for damage calc. |
| **Stat modifier** | `stat_modifier_reference` (in 03) | Reference values for stat calculations. |
| **Weapon type** | `weapon_type_stats` (in 03) | Weapon-type stat bonuses. |
| **Trial** | `trials`, `trial_bosses`, `trial_boss_set_notes` (in 03) | Trials, bosses, per-boss set notes. |

## Build (composition only)

| Table | Responsibility |
|-------|----------------|
| `recommended_builds` | One row = one recommended build: references to `game_build_id`, `class_id`, `role_id`, `race_id`, `mundus_id`, `food_id`, `potion_id`, plus score and optional weapon_type, simulation_target_id. |
| `recommended_build_equipment` | For that build, which set is in which slot (slot_id, set_id). |

To get full details for a build you join out to the component tables (races, item_sets, mundus_stones, foods, potions, etc.); the build tables only hold IDs and scores.

## Versioning

Where the game changes per patch, component data is keyed by `game_build_id` (e.g. `item_sets`, `skills`, `foods`). Stable reference data (e.g. `races`, `classes`, `equipment_slots`) has no `game_build_id`. So we lead with components and version only the ones that change.

## Creating the DB

From project root:

```bash
python scripts/create_db.py
```

Runs `schema/01_schema.sql`, `02_indexes.sql`, and `03_xlsx_driven_schema.sql` in order.
