# Core: stat block, damage formula, weapon type stats

- **stat_block**: Given (race, sets, food, potion, mundus) compute a `StatBlock` (max resources, weapon/spell damage, crit, penetration, recovery, etc.). Reads from `race_effects`, `mundus_stones`, `set_bonuses`, and optionally `foods`/`potions` (when `effect_json` is populated). Optional `front_bar_weapons=(main_hand_type, off_hand_type)` applies weapon-type bonuses (e.g. Twin Blade and Blunt). If `stat_modifier_reference` is populated (from ingest_xlsx), reference caps (e.g. crit damage) may be applied via **stat_reference**.
- **stat_reference**: `get_stat_reference(conn, game_build_id)` loads `stat_modifier_reference` by category; `get_reference_value_by_name(conn, game_build_id, category, name)` returns a single value. Used for caps or formula notes from the Standalone Damage Modifiers Calculator.
- **damage**: Given a `StatBlock` and a skill's `coefficient_json`, compute base damage and full damage per hit (crit, damage-done %, armor mitigation, target vulnerability).
- **weapon_type**: Weapon type stats and comparisons. Uses `weapon_type_stats` (Dual Wield Twin Blade and Blunt: dagger crit rating, mace penetration, sword WD/SD, axe crit damage). **Dual wield rule:** when main and off hand are different 1H types, effects from both apply at **half** strength; same type doubles the bonus.

- **weapon_enchant_tradeoff**: Compare impact of weapon enchants (glyphs) vs weapon poisons. Uses `glyphs.effect_json` and `weapon_poisons.effect_json` (damage, cooldown, DoT, debuff). `compare_glyph_vs_poison(...)` returns DPS contribution and recommendation. **Demo:** `python scripts/enchant_poison_tradeoff_demo.py [--glyph 1] [--poison 2] [--base-dps 80000]`. **API:** `GET /api/enchant_poison_tradeoff`, `GET /api/weapon_glyphs`, `GET /api/weapon_poisons`.

**Demo:** `python scripts/stat_block_damage_demo.py [--race-id N] [--mundus-id N] [--weapon-main TYPE] [--weapon-off TYPE] [--ability-id ID]`

**Weapon comparison:** `python scripts/weapon_comparison_demo.py` prints aggregated bonuses for two loadouts (e.g. 2 daggers vs dagger+mace).

- **slot_rules**: Equipment rules for 5+5+2 (two 5-piece sets + monster 2pc). `get_five_piece_sets`, `get_monster_sets`, `assign_slots`, `enumerate_valid_combos`; weapon slots 8/9 and 10/11 share set (12 logical slots).

- **subclassing**: `validate_subclass_lines(conn, recommended_build_id)` enforces at most 2 of 3 class skill-line slots from other classes; `count_other_class_slots` for reporting. `get_default_class_lines_for_class(conn, game_build_id, class_id)` returns the 3 class line (slot_ord, skill_line_id); `ensure_build_class_lines(conn, recommended_build_id)` fills recommended_build_class_lines with the build's base-class lines when empty (used by run_optimizer).

- **rotation**: `rotation_dps(conn, game_build_id, stat_block, ability_weights, ...)` – DPS = sum of (damage_per_hit(ability) * hits_per_sec). ability_weights = [(ability_id, hits_per_sec), ...]. Used by the optimizer for rotation-aware scoring. Also `dynamic_rotation_dps` for priority-based recast-on-expiry. `TRIAL_DUMMY_HP` (21M) and `fight_duration_sec(dps, target_hp)` for parse/trial dummy fight duration (see COMBAT_TIMING_AND_SIMULATION.md §10).

- **Ultimate usage**: Optimal bar assignment (passive/buff/debuff ultimate vs damage ultimate, front vs back bar) and tradeoff when the buff/debuff is on the back bar are documented in `docs/COMBAT_TIMING_AND_SIMULATION.md` §9. Scoring can plug in when bar layout exists (`recommended_build_scribed_skills`, slots 6 and 12 = ultimates).

- **Optimizer**: `scripts/run_optimizer.py` enumerates valid set combos; score by stat proxy (default) or **rotation DPS** with `--ability-ids` and optional `--rotation-weights` (e.g. `1.0,0.25` for spammable + DoT). Use `--mythic`, `--filter-redundant`; optional `--abilities`, `--skill-lines`. Writes top N to `recommended_builds` and `recommended_build_equipment`.

**Requirements:** DB must have `race_effects` (run `schema/13_seed_race_effects.sql` or `create_db.py`), `mundus_stones` (seed 10), `weapon_type_stats` (seed 14), and for damage-per-hit a skill with `coefficient_json` (from `ingest_skills_uesp.py`). For optimizer: `set_summary` and `set_item_slots` (UESP ingest or seed 15).
