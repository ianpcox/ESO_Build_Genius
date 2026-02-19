# ESO Build Genius – Data Sources Quick Reference

**Target patch:** **Patch 48** (Update 48). Use build label **`Update 48`** for ingest to keep data current. See [CURRENT_PATCH.md](CURRENT_PATCH.md).

**Authoritative source:** Game data is authoritative when it comes from **Zenimax-published ESO API** (API TXT and API patch notes; see [PATCH_SOURCES.md](PATCH_SOURCES.md)) or **direct extraction from game client files**. All other sources (UESP, wiki, xlsx) are community/datamined. For a full comparison of every data source used in this project against the Zenimax API and game files, see **[DATA_SOURCES_VS_ESO_API.md](DATA_SOURCES_VS_ESO_API.md)**.

## Recommendations

- **game_builds.label and api_version** – Use **Zenimax API TXT** and **patch notes** to set and validate `game_builds.label` (e.g. `Update 48`) and `api_version`. See [PATCH_SOURCES.md](PATCH_SOURCES.md) for per-patch resource URLs and usage.
- **Set / skill / food / potion catalogs** – Prefer an **addon-based exporter** (in-game API) for these catalogs where the Zenimax API TXT does not publish them. Use UESP ESO Log or wiki as fallback or when no addon export is available.
- **Skill coefficients** – Keep **UESP** (viewSkillCoef / skillCoef) for damage/heal coefficients; these are not exposed in the addon API. Use UESP for **validation** of other ingested data where applicable.
- Ingest scripts in `scripts/` follow these recommendations where applicable; see each script’s docstring and this doc for source details.

## Best sources (minimal recognition lag)

| Source | What to use it for | How it updates | URL |
|--------|--------------------|----------------|-----|
| **Your own addon export** | Sets, items, skills, buffs, mundus, food, potions – **primary source of truth** | Run addon after each patch; export JSON/Lua | N/A – you build it |
| **UESP Skill Coefficients** | Damage/heal equations for ~7k skills (MaxStat, MaxPower, ratios) | Community regression; updated with patches | [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php) (reference); **data** from [esolog exportJson skillCoef](https://esolog.uesp.net/exportJson.php?table=skillCoef) |
| **UESP ESO API** | Lua API version ↔ game build; function names for addon | Build-tagged (e.g. v101047); new version after patch | https://esoapi.uesp.net/index.html |
| **UESP ESO Log** | setSummary, minedItem, minedSkills – validate or fill gaps | Player uploads via uespLog addon | https://esolog.uesp.net/viewlog.php |

### UESP ESO Log – exportJson API (sets)

The ESO Log site exposes a **JSON export** for datamined tables. For item sets use:

- **URL:** `https://esolog.uesp.net/exportJson.php?table=setSummary`
- **Optional:** `&limit=N` to restrict rows (omit for full export).
- **Response:** `{ "numRecords": N, "setSummary": [ ... ] }` with one object per set.

**Per-record fields (setSummary):** `gameId` (game set id), `setName`, `indexName`, `setMaxEquipCount`, `setBonusCount`, `setBonusDesc1`..`setBonusDesc12`, `setBonusDesc` (full text), `itemSlots` (e.g. `"Weapons(All) Light(All) Medium(All) Heavy(All) Ring Neck Shield"` or `"Medium(Head)"` for monster helms), `type`, `category`, `sources` (often empty; used to infer set type).

**Ingest script:** `scripts/ingest_sets_uesp.py` fetches this URL and fills `set_summary`, `set_bonuses`, and `set_item_slots` (UESP-aligned table/column names) for a given game build. Run with `--build-label "Update 48"` (or `--build-id N`); use `--replace` to replace existing sets for that build. Requires a normal browser-like `User-Agent` (script sends one).

**buff_grants_set_bonus (set → buff mapping):** The *essence* of set item data for the optimizer: which set bonus (game_id + num_pieces) grants which buff. Not provided by the API; we derive it by **parsing** `set_bonuses.set_bonus_desc` for known buff names (e.g. "Major Berserk", "Minor Slayer"). **Pipeline:** (1) Ensure extended buff catalog: run `python scripts/create_db.py` (or at least run `schema/07b_seed_buffs_full.sql` against your DB) so buff_id 7–43 exist (Major/Minor Vulnerability, Aegis, Slayer, Courage, Protection, Expedition, Vitality, Resolve, Evasion, Endurance, Intellect, Fortitude, Mending, Prophecy, Savagery, Sorcery, Breach, Heroism). Without them, only the original 6 buffs are matched and you get far fewer rows.
(2) Ingest sets: `python scripts/ingest_sets_uesp.py --build-label "Update 48" [--replace]`. (3) Populate set→buff links: `python scripts/populate_buff_grants_set_bonus.py --build-label "Update 48" [--replace]`. Use `--replace` when re-running so grants are rebuilt from current set_bonuses. This gives you a comprehensive data store: every set in the game with at least one parseable buff in its bonus text will have rows in `buff_grants_set_bonus` for redundancy detection and recommendations.

### Other exportJson tables (same base URL)

Same site exposes more tables via `?table=TABLE` (optional `&limit=N`, and for some tables `&id=...` or `&ids=...`). Useful for ESO Build Genius:

| Table | Use for | Caveats |
|-------|---------|--------|
| **minedSkills** | Full skill/ability catalog: id, name, description, cost, castTime, skillLine, target, numCoefVars, type1..6, a1..c1, etc. **Includes NPC, item, and world abilities** – not all are player skills. | **126k+ rows**; use `&limit=N` or paginate for bulk. **We do not ingest minedSkills.** |
| **skillCoef** | **Subset of minedSkills with `numCoefVars>0`**: abilities that have damage/heal formula coefficients (type1, a1, b1, c1, R1, avg1, …). These are the skills in use for combat math (player and some NPC/companion). | **~7k rows** (e.g. UESP [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php) reports “7083 skills with valid coefficients”). **We ingest skillCoef only** via `ingest_skills_uesp.py` – not 126k. |
| **minedItemSummary** | Item summary by itemId (or filter by type, equipType, weaponType, armorType). | Requires `&id=...` or `&ids=...`; no full dump without many requests. |
| **minedItem** | Per-item detail (level, trait, link, etc.); joins to minedItemSummary. | Requires item id(s); API notes “far too slow” for large queries. |
| **skillTree** | Skill tree structure (abilityId). | Small; good for linking skills to lines. |
| **skillTooltips** | Tooltip text by id. | Optional for display/tooltips. |
| **playerSkills** | Subset of minedSkills with `isPlayer=1`; has **classType** and **skillLine** (text names). | **Subclassing:** use to verify our class skill_lines seed and to set `skills.skill_line_id` (see below). |
| **achievements**, **quest**, **book** | Achievements, quests, books. | Only if you add those domains later. |

**Subclassing and skill-line linking:** Our schema has `skill_lines` (class, weapon, guild) with `class_id` for class lines and `recommended_build_class_lines` (3 slots per build, at most 2 from other classes). ESO Log **playerSkills** provides `classType` (e.g. "Dragonknight", "Templar") and `skillLine` (e.g. "Earthen Heart", "Aedric Spear"). Run `python scripts/verify_skill_lines_esolog.py [--build-label "Update 48"]` to confirm our seed class lines match ESO Log. Optionally run `python scripts/link_skill_lines_from_esolog.py --build-label "Update 48"` after skill ingest to set `skills.skill_line_id` from playerSkills so buff coverage and subclassing use consistent line IDs.

Base URL: `https://esolog.uesp.net/exportJson.php?table=TABLE`. Send a browser-like `User-Agent` to avoid 403.

### UESP repos (uesp-esoapps, uesp-esolog) – what’s usable remotely vs locally

| Repo / component | What it does | Use in ESO Build Genius |
|------------------|--------------|-------------------------|
| **uesp-esolog** | PHP backend for esolog.uesp.net; **exportJson.php** is the JSON API we use for setSummary (and can use for minedSkills, skillCoef, etc.). | **Use remotely** – HTTP to exportJson.php. No local run needed. |
| **uesp-esoapps / EsoExportScripts** | Scripts (e.g. `esoextract.sh`, `gameextract.sh`, `CompareLangFiles.py`) that run **EsoExtractData.exe** to extract from ESO client files (MNF/DAT). Outputs maps, icons, LANG→CSV, etc. | **Local only.** Requires game files and Windows; no HTTP API. Use only if you run a local pipeline for LANG strings or assets. |
| **uesp-esoapps / EsoExtractData** | Windows CLI to extract from MNF, DAT, ZOSFT, LANG. Full extract is 100GB+ and slow. | **Local only.** Feeds EsoExportScripts and parseGlobals; no remote API. |
| **uesp-esoapps / parseGlobals** | Python: parses Lua (from EsoExtractData or globals dump) → HTML/txt for **esodata.uesp.net** (Lua API, globals, function list). | **Indirect.** esodata.uesp.net is updated from this; we use esodata/esoapi for API version and names, not for set/skill/item records. Running parseGlobals yourself needs extracted game files. |
| **uesp-esoapps / uespLogMonitor** | GUI to upload uespLog addon data to UESP (feeds esolog DB). | User-side; doesn’t give us new APIs. |
| **uesp-esoapps / ParseBooks, EsoParseTables, etc.** | Other parsers/extractors in the repo. | Per-tool; mostly local extraction, not HTTP. |

**Summary:** For this project, the only UESP “data extract” we can use **without** running game-file extraction is **esolog.uesp.net exportJson** (setSummary already ingested; minedSkills/skillCoef are good next candidates). EsoExportScripts and EsoExtractData are useful only if you set up a local pipeline with ESO client files.

## Secondary / fallback

| Source | What to use it for | Lag | URL |
|--------|--------------------|-----|-----|
| **ESO Sets API** | Set names, types, bonuses (REST/GraphQL) | Medium | https://eso-sets.herokuapp.com/sets |
| **LibSets (Baertram)** | Set data in Lua; parse for your DB | Medium – maintainer updates per patch | https://github.com/Baertram/LibSets |
| **ESO-Database game-data** | Optional: locations, nodes; may expand | Medium | https://game-data.eso-database.com |

## Local / project data (data/)

**Version status:** The xlsx files in `data/` are **not** confirmed to be Update 48. See **[data/XLSX_VERSION_NOTES.md](data/XLSX_VERSION_NOTES.md)** for what is in each file and how to update.

| File | Use for |
|------|--------|
| **Damage Skills (Update 38_39_40).xlsx** | Base tooltip, ADPS, Type, Cost, Time, Crux, Secondary Effect per skill; class and Top sheets. **Content is Update 39/40 (U41 linked in sheets)** – not Update 48. Use for structure/names; use `ingest_skills_uesp.py` (UESP skillCoef) for current coefficients. For Patch 48, prefer an xlsx updated for Update 48 when available. |
| **Harpooner's Wading Kilt Cheat Sheet.xlsx** | Trial/boss notes on when Kilt is good/bad/situational. Ingest into trial_boss_set_notes. Version unknown; verify against current trials for Patch 48. |
| **Standalone Damage Modifiers Calculator (ESO).xlsx** | **References for Stats** -> `stat_modifier_reference`; **Weapon Comparisons** -> `weapon_type_stats`. Ingest via `python scripts/ingest_xlsx.py --build-label "Update 48"`; use `--skip-weapon-comparisons` if the sheet layout differs. Version unknown; re-source from an Update 48–current calculator if stat/weapon values matter. |

## Reference / validation (do not drive optimizer)

| Source | Use for | URL |
|--------|---------|-----|
| **ESO-Hub** | Build ideas, set lists, guides | https://eso-hub.com |
| **ESO Skillbook** | Skill trees, cast time, target, cost; cross-check | https://eso-skillbook.com/ |
| **ESO-Sets** | Sets by weight, content type, DLC; set bonus text | https://eso-sets.com |
| **UESP Build Editor** | Full stat calculation, target stats (e.g. 18200 resistance), buffs | https://en.uesp.net/wiki/Online:Build_Editor |
| **Official patch notes** | “What changed” and build labelling | https://forums.elderscrollsonline.com/en/categories/patch-notes |

**Per-patch resources:** For each patch, Zenimax and ESOUI publish features, patch notes, API patch notes (attachment), and API TXT documentation (attachment). See [PATCH_SOURCES.md](PATCH_SOURCES.md) for the resource pattern, URL templates, and how to use them for `game_builds` and re-ingest. ESOUI attachments may require login; use env vars or a gitignored config for credentials—never commit them.

## Addon / extraction tools

| Tool | Purpose | Link |
|------|---------|------|
| **CombatMetrics** | Records and analyses combat; DPS/HPS parses, fight logs. Useful for calibrating our damage formula (e.g. LA coefficient, DoT timing) and validating stat block + coefficient math against real parses. Requires LibAddonMenu, LibCustomMenu, LibCombat; uses CombatMetricsFightData for saved fights. | [GitHub – Solinur/CombatMetrics](https://github.com/Solinur/CombatMetrics/tree/master) |
| **ESO Data Dumper** | Dump achievements, dyes; pattern for more | https://github.com/sevenseacat/eso_data_dumper |
| **Item Set Dumper** | Dump all item sets to SavedVariables | https://www.esoui.com/downloads/info3488-ItemSetDumper.html |
| **EsoExtractData** | Extract from game .mnf/.dat files (raw) | https://www.esoui.com/downloads/info1258-EsoExtractData.html |
| **uespLog** | Contributes to UESP esolog.uesp.net | https://github.com/uesp/uesp-esolog |

## Suggested ingestion order

For a single-command pipeline (create_db, fetch, ingest sets/buff_grants/skills, link_skills, ingest food_potions), use **`python scripts/run_pipeline.py --build-label "Update 48" --replace`**. See [PIPELINE.md](PIPELINE.md).

Manual order:

1. **Ingest item sets from UESP** – `python scripts/ingest_sets_uesp.py --build-label "Update 48" --replace` (uses exportJson.php?table=setSummary; Patch 48 current). Use `"Default"` if you prefer a generic label.
2. **Populate buff_grants_set_bonus** – `python scripts/populate_buff_grants_set_bonus.py --build-label "Update 48" --replace` (parses set_bonus_desc for buff names; run after set ingest so every set has set→buff links for recommendations).
3. **Implement or adopt addon** that dumps sets, items, and (if possible) skill/buff data → JSON per game build.
4. **Ingest scribing script catalog** (optional): `python scripts/fetch_scribe_effects_uesp.py` then `python scripts/ingest_scribe_effects.py` (67 Focus/Signature/Affix scripts per build from UESP Online:Scribing).
5. **Ingest skills and coefficients** from UESP ESO Log: `python scripts/ingest_skills_uesp.py --build-label "Update 48" --replace` (uses exportJson.php?table=skillCoef; **~7k skills** with valid coefficients – verify at [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php); Patch 48 current). We do **not** ingest minedSkills (126k+).
6. **Use ESO API version list** (esoapi.uesp.net/index.html) to detect new builds and trigger re-ingest.
7. **Use patch notes** to label builds (e.g. “Update 48 Incremental 3”) and to know when to re-run optimizer.

**Skills and coefficients:** Skill coefficients (viewSkillCoef / skillCoef) are stored **in the skills table** in `skills.coefficient_json`, not in a separate table. Rationale: the main use is “one skill row = one formula” for the damage calculator; a single JSON column keeps that as one read. If you later need to query “all skills with coefficient type X” or enforce strict schema per slot, you could add a `skill_coefficients` table (game_build_id, ability_id, coef_ord, type, a, b, c, R, avg) and populate it from the same ingest—but it’s not required for the stat block or damage formula. `scripts/ingest_skills_uesp.py` fetches the **skillCoef** table only (abilities with numCoefVars > 0 – **~7k rows**, not minedSkills’ 126k+). Each row is inserted into `skills` with `coefficient_json` as an array of `{ type, a, b, c, R, avg }` per coefficient slot (damage/heal formula). Verify expected count at [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php) or run `python scripts/check_skills_patch48.py`. Use `--limit N` for a partial run or omit for full ingest. Optional: **playerSkills** (isPlayer=1) for skill-line linking; we do **not** ingest **minedSkills** (full catalog, 126k+).

**Traits, glyphs, weapon poisons:** Schema in `01_schema.sql` (traits) and `11_traits_glyphs_poisons.sql` (glyphs, weapon_poisons). Seed in `12_seed_traits_glyphs_poisons.sql`. Build equipment has optional `trait_id`, `glyph_id`, `weapon_poison_id` per slot.

**Scribing (Focus, Signature, Affix scripts):** The full catalog (21 Focus, 20 Signature, 26 Affix) is **not** in the schema seed. **Authoritative source for script IDs/names** when accessible: Zenimax API (game Lua at **esoapi.uesp.net** under `ingame/crafting/`, e.g. `scribingdata.lua`). For the initial full catalog we use the **UESP wiki** [Online:Scribing](https://en.uesp.net/wiki/Online:Scribing). Run `python scripts/fetch_scribe_effects_uesp.py` to write `data/scribe_effects.json`, then `python scripts/ingest_scribe_effects.py` to populate `scribe_effects` for every `game_build_id` (67 scripts per build; stable IDs: Focus 1–21, Signature 22–41, Affix 42–67). Optional later: fill `skill_scribe_compatibility` from game Lua or community data when available.

**Mundus, food, potion:** Seed data for all 13 mundus stones (from UESP wiki [Online:Mundus_Stones](https://en.uesp.net/wiki/Online:Mundus_Stones)) plus minimal food and potion rows lives in `schema/10_seed_mundus_food_potions.sql`. To add more foods or potions: (1) **Foods** – run `python scripts/fetch_foods_uesp.py` to write `data/foods.json`, then ingest with `--foods-json data/foods.json`. (2) **Potions** – run `python scripts/fetch_potions_uesp.py` to write `data/potions.json` from UESP [Online:Potions](https://en.uesp.net/wiki/Online:Potions), then ingest with `--potions-json data/potions.json`. Use `scripts/ingest_food_potions.py --build-label "Update 48" --foods-json data/foods.json --potions-json data/potions.json --replace`. Expect JSON arrays of objects with `food_id`/`potion_id`, `name`, `duration_sec`, `effect_text`, and for potions `cooldown_sec`.

**Race effects (racial passives):** Seed data for all 10 races (4 passives each) lives in `schema/13_seed_race_effects.sql`. Source: UESP wiki race pages (e.g. [Online:High_Elf](https://en.uesp.net/wiki/Online:High_Elf), [Online:Breton](https://en.uesp.net/wiki/Online:Breton), [Online:Races](https://en.uesp.net/wiki/Online:Races)). Descriptions are max-rank (rank 3) tooltip text; `effect_type` is the passive name (e.g. Highborn, Spell Recharge). Applied automatically when you run `python scripts/create_db.py` (all schema files run in order). No separate ingest script; re-run create_db or execute the seed file against an existing DB to refresh race_effects for every `game_builds` row.

---

## Trial boss and trash pack data (standalone source – required for per-trial, per-boss optimisation)

To optimise **per trial boss** we need **data for each trial boss**: e.g. resistance, HP, phase structure, and mechanics that affect set or build choice (invuln windows, movement, Stagger, etc.). The current schema has `trials` and `trial_bosses` (name only); we do not yet have a filled source for per-boss stats or behaviour.

To optimise **trash packs** (AOE between bosses) we need **pack composition** and **individual enemy types** within each pack: which enemies appear together, in what counts, and their resistances/HP so we can model cleave and AOE value. That is trial- and pack-specific and is not provided by UESP set/skill ingest.

**Likely a separate standalone data source:** Community spreadsheets, addon export (e.g. combat log or encounter data), or manually maintained tables. Once we have a source we can:

- **Bosses:** Extend `trial_bosses` or link to `simulation_targets` (e.g. resistance, hp, simulation_target_id, optional mechanics notes) and ingest per-boss rows.
- **Trash:** Add tables such as `trial_trash_packs` (trial_id, pack_id or name/ord, optional link to simulation_target) and `trial_trash_pack_enemies` (pack_id, enemy_type_id or name, count or weight) so we know pack composition and enemy types per pack for AOE scoring.

Schema can be extended when this standalone source is available; until then, optimisation uses the generic `simulation_targets` (e.g. trial_dummy_21m, trial_trash_generic) without per-boss or per-pack detail.

**Verification against ESO Log (esolog.uesp.net):** The public **exportJson** API ([exportJson.php](https://github.com/uesp/uesp-esolog/blob/master/exportJson.php)) only exposes a fixed set of tables: `setSummary`, `skillCoef`, `minedSkills`, `minedItem`, `minedItemSummary`, `achievements`, `achievementCategories`, `achievementCriteria`, `book`, `quest`, `questCondition`, `questItem`, `questReward`, `questStep`, `uniqueQuest`, `skillTree`, `skillTooltips`, `playerSkills`, `cpSkills`, `cpSkillDescriptions`. It does **not** expose trial, boss, zone, encounter, or npcLocations tables. Therefore **trial boss and trash pack data cannot be verified or ingested from ESO Log** with the current API. Our seed (schema 16 and 18) is built from the **UESP wiki** ([Online:Trials](https://en.uesp.net/wiki/Online:Trials), per-trial pages such as Online:Cloudrest, Online:Rockgrove). To re-verify or update trial/boss/trash data, use the wiki or a future standalone source; if UESP adds trial/boss/encounter exports to exportJson, we can add an ingest script. Run `python scripts/verify_esolog_trials.py` to confirm that esolog returns an error for invalid table names such as `trial` or `zones`.

---

## Build scope and current gaps

| Area | In schema / builds? | Notes |
|------|---------------------|------|
| **Foods / drinks** | Yes | **Full list** from UESP: run `python scripts/fetch_foods_uesp.py` to write `data/foods.json` (~575 recipes), then `python scripts/ingest_food_potions.py --build-label "Update 48" --foods-json data/foods.json --replace`. Seed still has 3 minimal foods in `10_seed_mundus_food_potions.sql` for fresh DBs; replace with full list per build as above. |
| **Potions** | Yes | **Full list** from UESP: run `python scripts/fetch_potions_uesp.py` to write `data/potions.json` (~60 potions from [Online:Potions](https://en.uesp.net/wiki/Online:Potions)), then `python scripts/ingest_food_potions.py --build-label "Update 48" --potions-json data/potions.json --replace`. Seed has 3 minimal potions; replace with full list per build as above. |
| **Weapon enchantments (glyphs)** | Yes | **In schema.** Table `glyphs` (game_build_id, glyph_id, name, effect_text, slot_kind). Seed in `12_seed_traits_glyphs_poisons.sql`. `recommended_build_equipment.glyph_id` links to glyph (nullable). |
| **Weapon poisons** | Yes | **In schema.** Table `weapon_poisons` (game_build_id, poison_id, name, effect_text, duration_sec). Seed in `12_seed_traits_glyphs_poisons.sql`. `recommended_build_equipment.weapon_poison_id` (nullable). |
| **Weapon / armor traits** | Yes | **In schema.** Table `traits` (id, name, slot_type: weapon/armor/jewelry). Seed in `12_seed_traits_glyphs_poisons.sql`. `recommended_build_equipment.trait_id` (nullable). |
| **Scribing (Focus/Signature/Affix)** | Yes | **Ingest:** Run `fetch_scribe_effects_uesp.py` then `ingest_scribe_effects.py` to fill `scribe_effects` (67 scripts from UESP [Online:Scribing](https://en.uesp.net/wiki/Online:Scribing)). Zenimax API (esoapi.uesp.net ingame/crafting/scribingdata.lua) is authoritative for script IDs when available. |
| **Skills / coefficients** | Yes | **Ingest:** `python scripts/ingest_skills_uesp.py --build-label "Update 48" --replace`. Fills `skills` from UESP esolog **skillCoef only** (~7k abilities with valid coefficients – same set as [viewSkillCoef](https://esoitem.uesp.net/viewSkillCoef.php); not minedSkills’ 126k+). `coefficient_json`: type, a, b, c, R, avg per slot for damage/heal math. Verify: `python scripts/check_skills_patch48.py`. |
| **Race effects** | Yes | **Seed:** `schema/13_seed_race_effects.sql`. Populates `race_effects` (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude) from UESP wiki race pages. One row per passive per race per build; 4 passives per race (max-rank descriptions). Applied by `create_db.py`. Needed for stat block (race → derived stats). |
| **buff_grants_set_bonus** | Yes | **Source:** Parsed from `set_bonuses.set_bonus_desc` (UESP setSummary). **Pipeline:** After `ingest_sets_uesp.py`, run `populate_buff_grants_set_bonus.py --build-label "Update 48" [--replace]`. Requires extended buff catalog (07 + 07b). Comprehensive store: every set with a parseable Major/Minor buff in its bonus text gets set→buff rows for redundancy and recommendations. |
| **Trial boss data** | Gap | **Required for per-boss optimisation.** Data per trial boss: resistance, HP, mechanics. Likely **standalone source** (community, addon, or manual). Schema: extend `trial_bosses` or link to `simulation_targets` when source available. |
| **Trash pack data** | Gap | **Required for trash AOE optimisation.** Pack composition and enemy types per pack (which enemies, counts). Likely **standalone source**. Schema: e.g. `trial_trash_packs`, `trial_trash_pack_enemies` when source available. |

Optimizer and UI can use trait, glyph, weapon poison, skill coefficients, race effects, and set→buff grants for stat math and recommendations. Per-trial, per-boss and per-pack optimisation will require the trial boss and trash pack data source above.

---

This keeps your pipeline **patch-aware** and minimizes dependence on third-party sites updating on their own schedule.
