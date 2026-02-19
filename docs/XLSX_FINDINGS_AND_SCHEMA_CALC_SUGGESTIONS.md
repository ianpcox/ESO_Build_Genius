# Findings from xlsx Files and Suggestions for Schema and Calculations

Based on a detailed read of the three workbooks in `data/`, plus [UESP Build Editor](https://en.uesp.net/wiki/Online:Build_Editor), [ESO Skillbook](https://eso-skillbook.com/), and [ESO-Sets](https://eso-sets.com). This doc drives schema changes and damage/modifier calculations.

---

## 1. Damage Skills (Update 38_39_40).xlsx

### Structure
- **Per-class sheets** (Arcanist, Dragonknight, Necromancer, etc.): three skill-line blocks per sheet (e.g. class, Two Handed, Soul Magic; then weapon/guild lines). Columns repeat in blocks: **Skill Line/Name**, **Base Tooltip**, **ADPS**, **Type**, **Range**, **Cost**, **Time**, **Crux** (Arcanist), **Secondary Effect**.
- **"Top" sheets** (e.g. Arcanist Top, DK Top): same columns, one block; skills ranked by **ADPS** (adjusted DPS for DoTs).
- **ADPS definition** (from sheet footnote): *"This is the adjusted DPS of a damage over time skill when accounting for spammable casts lost in accordance with the duration. EX: 10s DoTs Lose 6 Spammables per minute, 20s DoTs Lose 3 Spammables per minute, 30s DoTs Lose 2 Spammables per minute, etc."*

### Key fields for schema and calc
| Field | Meaning | Use in DB/calc |
|-------|--------|-----------------|
| **Base Tooltip** | Numeric tooltip damage at some reference stat assumption | Store as `base_tooltip`; use as reference or with coefficient for damage formula. |
| **ADPS** | DoT DPS minus opportunity cost (spammables lost per minute) | Store for ranking; replicate formula for simulation. |
| **Type** | e.g. AoE DoT, ST Direct, ST Direct + ST DoT, AoE Direct | Categorise for rotation (DoT vs spammable vs channel). |
| **Range** | e.g. 28m, 5m r, 18m x 8m | Optional for targeting rules. |
| **Cost** | Resource (e.g. 2295, 2700) | Sustain and rotation. |
| **Time** | Duration (seconds) for DoTs, or cast time (e.g. 0.8) for spammables | `duration_sec` and/or `cast_time_sec`; drives ADPS and GCD usage. |
| **Crux** | Builder/Spender, 3 Crux variant | Arcanist-only; store for skill variant. |
| **Secondary Effect** | Buffs, debuffs, synergies | Text; later parse for buff/debuff IDs. |

### ADPS calculation (to implement)
- **Spammables per minute** at 1 s GCD = 60.
- DoT with duration **D** seconds is recast every **D** seconds → **60/D** casts per minute → **60 - 60/D** spammable slots left per minute.
- So **spammables lost per minute** = **60/D** (e.g. D=10 → 6, D=20 → 3).
- **Opportunity cost** = (spammables lost per minute) × (damage per spammable cast) / 60 = spammable DPS lost.
- **ADPS** = (DoT total damage over duration / D) − (spammable DPS lost). Negative ADPS means the DoT is worse than just spamming.

---

## 2. Harpooner's Wading Kilt Cheat Sheet.xlsx

### Structure
- **Sheet1:** Trial name (vMoL, vHoF, vCR, etc.), **Boss name**, Non-HM/HM columns (often empty), long **notes** on when Harpooner's Wading Kilt is good/bad/situational per boss (stack maintenance, add control, etc.).

### Schema idea
- **trial_boss_set_notes** (or **mythic_situational_notes**): `trial_id`, `boss_id` (or name), `game_id` (mythic/set), `note_type` ('good'|'bad'|'situational'), `note_text`. Populate from this sheet so the optimizer or UI can warn “Kilt is bad here” per boss.

---

## 3. Standalone Damage Modifiers Calculator (ESO).xlsx

### Main Sheet
- **Inputs:** Crit Chance (e.g. 0.5), Crit Damage (1.0), Max Resource (33000), Wpn/Spl Dmg (7000), % Damage Done (0.15), % Damage Taken (0.15), **Penetration (18200)**.
- **Output:** Example hit values (Non-Crit, Crit, Avg Value) from a base hit.
- **Use:** Our damage formula should take the same inputs and produce the same non-crit/crit/avg pattern. 18200 is default vet dungeon boss resistance (matches UESP Build Editor).

### Weapon Comparisons
- Rows per **weapon type**: DW (Nirn/Precise, Nirn/Charged), 2H Greatsword, Bow (Melee, Ranged), Inferno Staff, Lightning Staff.
- Columns: **Total Wpn/Spl Dmg**, **Total Crit Chance**, **Bonus % Done**, **Status Chance +**, **Other (A/B/C)** (e.g. 1 Extra Enchantment, Major Evasion, Hawk Eye, 2974 Pen staff skills).
- Note: *"Weapon/Spell Damage is after % Bonuses (Maj/Minor Brutality, 6 Medium, 3 Fighters Guild)"*; *"Crit Chance is given the baseline of the full Precise trait which adds 7.2% Critical Chance"*.
- **Use:** Store **weapon_type** on build (or slot); apply the correct bonus set (Precise 7.2%, etc.) when computing stat block and when comparing weapon types (e.g. “% Below DW”).

### Set Bonus Comparisons
- Rows: specific bonuses (e.g. **1487 Penetration**, **771 Crit Chance (Slimecraw)**, **657 Crit Chance**, **191 Wpn/Spl Dmg**, **129 + % Boosts**, **1291 Max Resource**, **1096 + % Boosts**).
- Columns: **Boost**, **Starting Amount before Bonuses**, and a **multiplier** (e.g. 0.031, 0.046) – marginal damage increase from that bonus.
- **Use:** Penetration has diminishing returns (e.g. 1487 pen from 0 → 0.031; from 16713 → different; from 700 → 0.046). We need a **mitigation/penetration curve** (damage multiplier vs target effective resistance after pen) and, optionally, a table of (starting_stat, bonus, marginal_gain) for set bonus comparison.

### References for Stats
- **Set bonuses:** e.g. Stamina/Magicka 1096 → 1249.44 with modifiers; Wpn/Spl Dmg 129 → 190.92; Crit Chance 0.03; Penetration 1487.
- **Racial bonuses:** Stamina/Magicka (2000, 1910, 1000, 915), Wpn/Spl Dmg 258, Crit Damage 0.12.
- **Named bonuses:** Powerful Assault 307→454.36, Minor Courage 215→318.2, Major Courage 430→636.4, Spaulder of Ruin 260→384.8, Berserker Glyph 452→668.96.
- **Base stats:** Crit Chance 0.10, Crit Damage 0.50, Max Resource 12000, Wpn/Spl Dmg 1000.
- **% Buffs/Debuffs:** Major Berserk 0.10, Major Slayer 0.10, Minor Berserk 0.05, Minor Slayer 0.05, Major Vuln 0.10, Minor Vuln 0.05, Z'en 0.05, etc.
- **Max Resource modifiers:** Warhorn 0.10, Undaunted 0.04, Inner Light 0.07, Siphoning/Bound Armaments 0.08.
- **Wpn/Spl Dmg modifiers:** Major Sorcery/Brutality 0.20, Minor 0.10, Medium Armor 0.02 per piece (×6), Fighters Guild 0.03 per skill (×2), Sorcerer 0.02, Templar 0.06.

**Use:** Ingest as **reference data** so we can build the full stat block from race + sets + buffs + weapon type + CP (later). One table for “stat modifiers” (name, category, base_value, modifier_formula or effective_value) and use it in a **stat block calculator**.

---

## 4. UESP Build Editor (and Combat) takeaways

- **Target stats:** Resistance (default 18200), % Crit Resist, Flat Crit Resist, % Critical, % Attack Bonus, % Defense Bonus, % Critical Damage, % Penetration, Flat Penetration. We should have a **simulation_target** or **target_stats** table keyed by build or scenario (e.g. “vet dungeon boss”, “trial dummy”).
- **Effective Spell/Weapon Power:** Custom stat representing potential DPS; raising by X% ≈ X% more DPS. We can expose the same idea from our formula.
- **Buffs tab:** Predefined buffs, including “(Target)” for debuffs on target – aligns with our `buffs` table and damage formula (1 + Damage Taken).

---

## 5. Schema suggestions (concrete)

### 5.1 Skills table (add columns)
- `base_tooltip` REAL – reference tooltip at standard stats (from Damage Skills xlsx).
- `adps` REAL – adjusted DPS for DoTs (nullable).
- `skill_damage_type` TEXT – e.g. 'ST Direct', 'AoE DoT', 'ST Direct + ST DoT'.
- `range_text` TEXT – e.g. '28m', '5m r'.
- `cost` INTEGER – resource cost.
- `duration_sec` REAL – DoT/channel duration.
- `cast_time_sec` REAL – cast time (e.g. 0.8 for spammables).
- `crux_required` INTEGER – Arcanist (nullable).
- `data_source` TEXT – e.g. 'damage_skills_u38_40', 'uesp_coef'.
- `update_label` TEXT – e.g. 'Update 39'.

### 5.2 New tables

**simulation_targets**  
- `id`, `name` (e.g. 'vet_dungeon_boss', 'trial_dummy_21M'), `resistance`, `crit_resist_pct`, `flat_crit_resist`, `penetration_pct`, `flat_penetration`, `notes`.

**stat_modifier_reference**  
- `game_build_id`, `category` ('set_bonus'|'racial'|'named_bonus'|'buff_pct'|'resource_modifier'|'damage_modifier'), `name`, `base_value`, `effective_value` or `formula`, `notes`.  
- Feeds the stat block calculator (References for Stats).

**weapon_type_stats**  
- `game_build_id`, `weapon_type` (e.g. 'dw_nirn_precise', 'inferno_staff'), `bonus_wd_sd`, `bonus_crit_chance`, `bonus_pct_done`, `notes`.  
- From Weapon Comparisons; applied when build has that weapon type.

**trial_boss_set_notes**  
- `trial_id`, `boss_id` (or `boss_name`), `game_id`, `note_type` ('good'|'bad'|'situational'), `note_text`.  
- From Kilt cheat sheet; can extend to other mythics/sets.

**champion_point_trees** (later)  
- For CP allocation and CP-based modifiers (Elemental Expert, etc.); referenced by optimizer once we add CP.

### 5.3 Recommended_builds (add columns)
- `weapon_type` TEXT – e.g. 'dw_nirn_precise', 'inferno_staff'.
- `simulation_target_id` INTEGER – FK to simulation_targets.
- Optional: `cp_snapshot_json` or FK to cp_allocation for future.

---

## 6. Calculation suggestions

### 6.1 Single-hit damage (align with Main Sheet)
- **Inputs:** crit_chance, crit_damage, max_resource, weapon_spell_damage, pct_damage_done, pct_damage_taken, penetration, target_resistance, skill_base_damage (from coefficient or base_tooltip).
- **Base** = f(skill_base_damage, max_resource, weapon_spell_damage) using same ratio as UESP (e.g. 10.46).
- **Mitigation** = resistance_curve(target_resistance - penetration) – implement the same curve the Calculator uses (or armour mitigation formula from forum).
- **Non-crit** = Base × (1 + pct_damage_done) × (1 + pct_damage_taken) × Mitigation.
- **Crit** = Non-crit × (1 + crit_damage).
- **Avg** = Non-crit × (1 + crit_chance × crit_damage).

### 6.2 Stat block from build
- Sum **flat** stats from race, sets, food, mundus, named bonuses (using stat_modifier_reference).
- Apply **% modifiers** in the order the game uses (References: Warhorn, Undaunted, Inner Light for max resource; Major/Minor Sorcery/Brutality, medium armor, Fighters Guild, etc. for weapon/spell damage).
- Apply **weapon_type_stats** for the chosen weapon (Precise 7.2%, etc.).
- Output: max_resource, weapon_spell_damage, crit_chance, crit_damage, penetration, pct_damage_done (from buffs), etc.

### 6.3 ADPS for DoTs
- **Spammables lost per minute** = 60 / duration_sec.
- **Spammable damage per cast** = single-hit avg damage for chosen spammable (from formula above).
- **Opportunity cost DPS** = (60 / duration_sec) × spammable_damage_per_cast / 60.
- **DoT total damage** = from skill (base_tooltip or coefficient over duration).
- **ADPS** = (DoT total / duration_sec) − opportunity_cost_DPS. Use when ranking DoTs or comparing to spammable.

### 6.4 Penetration / mitigation curve
- From Set Bonus Comparisons: marginal value of 1487 pen depends on current target effective resistance. Implement **mitigation(resistance)** (e.g. 1 − resistance/(resistance + constant) or game’s actual formula) and **marginal_gain(current_pen, bonus_pen, target_resistance)** so set bonuses that add pen can be compared correctly.

### 6.5 Weapon-type comparison
- Store “baseline” weapon (e.g. DW Nirn/Precise) and compute “% Below DW” for other weapon types using the same stat block and the Weapon Comparisons logic (and note about extra enchant, Hawk Eye, etc.) so we can compare builds across weapon types.

---

## 7. Additional resources to track

- **[ESO Skillbook](https://eso-skillbook.com/)** – Skill trees, cast time (e.g. 400 ms, 1000 ms), target, cost; useful for cross-check and cast times.
- **[ESO-Sets](https://eso-sets.com)** – Sets by weight, content type, DLC; set bonus text; good for validation and set_type/source.
- **[UESP Build Editor](https://en.uesp.net/wiki/Online:Build_Editor)** – Full stat calculation and target stats; **[Special:EsoBuildEditor](https://en.uesp.net/wiki/Special:EsoBuildEditor)** – live tool.

These can be added to `DATA_SOURCES.md` as reference/validation; ingestion priority remains addon export + UESP skill coefficients + your xlsx for base_tooltip/ADPS and modifier reference.

---

## 8. Suggested implementation order

1. **Schema:** Add new columns to `skills`; add tables `simulation_targets`, `stat_modifier_reference`, `weapon_type_stats`, `trial_boss_set_notes`.
2. **Ingest:** Script to load Damage Skills xlsx into `skills` (and optionally a staging table keyed by update); load References for Stats (and Set Bonus Comparisons) into `stat_modifier_reference`; load Kilt sheet into `trial_boss_set_notes` (with trial/boss names); load Weapon Comparisons into `weapon_type_stats`.
3. **Calc:** Implement single-hit damage (Main Sheet), then stat block from build (References), then ADPS (Damage Skills), then mitigation curve (Set Bonus Comparisons).
4. **Optimizer:** Use stat block + damage formula + ADPS for DoT vs spammable choice; use weapon_type and simulation_target when comparing builds.
