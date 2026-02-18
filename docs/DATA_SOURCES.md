# ESO Build Genius – Data Sources Quick Reference

## Best sources (minimal recognition lag)

| Source | What to use it for | How it updates | URL |
|--------|--------------------|----------------|-----|
| **Your own addon export** | Sets, items, skills, buffs, mundus, food, potions – **primary source of truth** | Run addon after each patch; export JSON/Lua | N/A – you build it |
| **UESP Skill Coefficients** | Damage/heal equations for ~7k skills (MaxStat, MaxPower, ratios) | Community regression; updated with patches | https://esoitem.uesp.net/viewSkillCoef.php |
| **UESP ESO API** | Lua API version ↔ game build; function names for addon | Build-tagged (e.g. v101047); new version after patch | https://esoapi.uesp.net/index.html |
| **UESP ESO Log** | setSummary, minedItem, minedSkills – validate or fill gaps | Player uploads via uespLog addon | https://esolog.uesp.net/viewlog.php |

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

1. **Implement or adopt addon** that dumps sets, items, and (if possible) skill/buff data → JSON per game build.
2. **Ingest skill coefficients** from UESP (esoitem.uesp.net/viewSkillCoef.php) – scrape or manual export; store by build/date.
3. **Use ESO API version list** (esoapi.uesp.net/index.html) to detect new builds and trigger re-ingest.
4. **Use patch notes** to label builds (e.g. “Update 48 Incremental 3”) and to know when to re-run optimizer.

This keeps your pipeline **patch-aware** and minimizes dependence on third-party sites updating on their own schedule.
