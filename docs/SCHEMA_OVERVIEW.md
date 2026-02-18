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
| **Skill** | `skills` | Skills/abilities and coefficients, tooltips, cost, duration. Linked to `skill_lines` via skill_line_id. |
| **Skill line** | `skill_line_types`, `skill_lines`, `skill_line_passives` (04) | Skill lines (class, weapon, guild, world, scribed); class lines owned by a class; passives per line. |
| **Buff** | `buffs` | Buffs/debuffs (name, effect type, magnitude). Standalone; sources linked via `buff_grants`. |
| **Buff grants** | `buff_grants` (04), `buff_grants_set_bonus` (06) | Links buffs to abilities, skill-line passives, and set bonuses. Used to avoid duplicate buff sources when optimizing (e.g. Combat Prayer vs Kinras both grant Minor Berserk). |
| **Target type** | `target_types`, `skill_target_bonus` (04) | Target granularity (Undead, Daedra, etc.) and which skills get a bonus vs. which types. |
| **Scribing** | `scribe_effect_slots`, `scribe_effects`, `skill_scribe_compatibility`, `recommended_build_scribed_skills` (05) | Base skill + up to 3 additional effects (Focus, Signature, Affix); catalog and per-build bar layout with scribed variants. |
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
| `recommended_build_class_lines` (04) | **Subclassing:** which 3 class skill lines this build uses (slot_ord 1..3, skill_line_id). Base class is in recommended_builds.class_id; up to 2 of the 3 lines may be from other classes. |
| `recommended_build_scribed_skills` (05) | **Scribing:** per bar slot, base ability_id + 0..3 scribe_effect_ids. Records which scribed variant of each skill is on the build; multiplies build diversity and complicates "optimal". |

To get full details for a build you join out to the component tables (races, item_sets, mundus_stones, foods, potions, etc.); the build tables only hold IDs and scores.

## Versioning

Where the game changes per patch, component data is keyed by `game_build_id` (e.g. `item_sets`, `skills`, `foods`). Stable reference data (e.g. `races`, `classes`, `equipment_slots`) has no `game_build_id`. So we lead with components and version only the ones that change.

## Creating the DB

From project root:

```bash
python scripts/create_db.py
```

Runs all `schema/*.sql` in order (01 through 08). Schema 07 seeds class skill lines, minimal buffs, and one example set (Kinras) + buff_grants_set_bonus. Schema 08 adds jewelry slots (neck, ring1, ring2) for 14-slot equipment layout.
