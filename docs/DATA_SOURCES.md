# ESO Build Genius – Data Sources Quick Reference

## Best sources (minimal recognition lag)

| Source | What to use it for | How it updates | URL |
|--------|--------------------|----------------|-----|
| **Your own addon export** | Sets, items, skills, buffs, mundus, food, potions – **primary source of truth** | Run addon after each patch; export JSON/Lua | N/A – you build it |
| **UESP Skill Coefficients** | Damage/heal equations for ~7k skills (MaxStat, MaxPower, ratios) | Community regression; updated with patches | https://esoitem.uesp.net/viewSkillCoef.php |
| **UESP ESO API** | Lua API version ↔ game build; function names for addon | Build-tagged (e.g. v101047); new version after patch | https://esoapi.uesp.net/index.html |
| **UESP ESO Log** | setSummary, minedItem, minedSkills – validate or fill gaps | Player uploads via uespLog addon | https://esolog.uesp.net/viewlog.php |

### UESP ESO Log – exportJson API (sets)

The ESO Log site exposes a **JSON export** for datamined tables. For item sets use:

- **URL:** `https://esolog.uesp.net/exportJson.php?table=setSummary`
- **Optional:** `&limit=N` to restrict rows (omit for full export).
- **Response:** `{ "numRecords": N, "setSummary": [ ... ] }` with one object per set.

**Per-record fields (setSummary):** `gameId` (game set id), `setName`, `indexName`, `setMaxEquipCount`, `setBonusCount`, `setBonusDesc1`..`setBonusDesc12`, `setBonusDesc` (full text), `itemSlots` (e.g. `"Weapons(All) Light(All) Medium(All) Heavy(All) Ring Neck Shield"` or `"Medium(Head)"` for monster helms), `type`, `category`, `sources` (often empty; used to infer set type).

**Ingest script:** `scripts/ingest_sets_uesp.py` fetches this URL and fills `item_sets`, `set_bonuses`, and `set_slots` for a given game build. Run with `--build-label "Default"` (or `--build-id N`); use `--replace` to replace existing sets for that build. Requires a normal browser-like `User-Agent` (script sends one).

### Other exportJson tables (same base URL)

Same site exposes more tables via `?table=TABLE` (optional `&limit=N`, and for some tables `&id=...` or `&ids=...`). Useful for ESO Build Genius:

| Table | Use for | Caveats |
|-------|---------|--------|
| **minedSkills** | Full skill/ability catalog: id, name, description, cost, castTime, skillLine, target, numCoefVars, type1..6, a1..c1, etc. | 126k+ rows; use `&limit=N` or paginate for bulk. |
| **skillCoef** | Subset of minedSkills with `numCoefVars>0`: damage/heal formula coefficients (type1, a1, b1, c1, R1, avg1, …). | Ideal for stat block / damage calc; same limit/pagination. |
| **minedItemSummary** | Item summary by itemId (or filter by type, equipType, weaponType, armorType). | Requires `&id=...` or `&ids=...`; no full dump without many requests. |
| **minedItem** | Per-item detail (level, trait, link, etc.); joins to minedItemSummary. | Requires item id(s); API notes “far too slow” for large queries. |
| **skillTree** | Skill tree structure (abilityId). | Small; good for linking skills to lines. |
| **skillTooltips** | Tooltip text by id. | Optional for display/tooltips. |
| **playerSkills** | Subset of minedSkills with `isPlayer=1`. | Player-usable skills only. |
| **achievements**, **quest**, **book** | Achievements, quests, books. | Only if you add those domains later. |

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

| File | Use for |
|------|--------|
| **Damage Skills (Update 38_39_40).xlsx** | Base tooltip, ADPS, Type, Cost, Time, Crux, Secondary Effect per skill; class and Top sheets. Drives skills columns and ADPS formula. |
| **Harpooner's Wading Kilt Cheat Sheet.xlsx** | Trial/boss notes on when Kilt is good/bad/situational. Ingest into trial_boss_set_notes. |
| **Standalone Damage Modifiers Calculator (ESO).xlsx** | Main Sheet: crit, max resource, Wpn/Spl Dmg, percent done/taken, penetration. Weapon Comparisons, Set Bonus Comparisons, References for Stats for stat block and modifier reference. |

## Reference / validation (do not drive optimizer)

| Source | Use for | URL |
|--------|---------|-----|
| **ESO-Hub** | Build ideas, set lists, guides | https://eso-hub.com |
| **ESO Skillbook** | Skill trees, cast time, target, cost; cross-check | https://eso-skillbook.com/ |
| **ESO-Sets** | Sets by weight, content type, DLC; set bonus text | https://eso-sets.com |
| **UESP Build Editor** | Full stat calculation, target stats (e.g. 18200 resistance), buffs | https://en.uesp.net/wiki/Online:Build_Editor |
| **Official patch notes** | “What changed” and build labelling | https://forums.elderscrollsonline.com/en/categories/patch-notes |

## Addon / extraction tools

| Tool | Purpose | Link |
|------|---------|------|
| **ESO Data Dumper** | Dump achievements, dyes; pattern for more | https://github.com/sevenseacat/eso_data_dumper |
| **Item Set Dumper** | Dump all item sets to SavedVariables | https://www.esoui.com/downloads/info3488-ItemSetDumper.html |
| **EsoExtractData** | Extract from game .mnf/.dat files (raw) | https://www.esoui.com/downloads/info1258-EsoExtractData.html |
| **uespLog** | Contributes to UESP esolog.uesp.net | https://github.com/uesp/uesp-esolog |

## Suggested ingestion order

1. **Ingest item sets from UESP** – `python scripts/ingest_sets_uesp.py --build-label "Default" --replace` (uses exportJson.php?table=setSummary; ~706 sets).
2. **Implement or adopt addon** that dumps sets, items, and (if possible) skill/buff data → JSON per game build.
3. **Ingest skill coefficients** from UESP (esoitem.uesp.net/viewSkillCoef.php) – scrape or manual export; store by build/date.
4. **Use ESO API version list** (esoapi.uesp.net/index.html) to detect new builds and trigger re-ingest.
5. **Use patch notes** to label builds (e.g. “Update 48 Incremental 3”) and to know when to re-run optimizer.

**Possible next UESP exportJson ingests:** minedSkills or skillCoef (skills + damage coefficients; use `&limit=` or paginate), or minedItemSummary for specific item ids, to backfill or validate `skills` and skill damage formulae.

This keeps your pipeline **patch-aware** and minimizes dependence on third-party sites updating on their own schedule.
