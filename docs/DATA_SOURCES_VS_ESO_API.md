# Data sources vs Zenimax ESO API (authoritative)

**Authority rule:** Game data is **authoritative** when it comes from (1) **Zenimax-published ESO API** (API TXT documentation and API patch notes, per patch, as referenced in [PATCH_SOURCES.md](PATCH_SOURCES.md)), or (2) **direct extraction from game client files** (e.g. ESO install folder via EsoExtractData / UESP tooling). All other sources are community/datamined and should be compared or validated against the API (or game files) where possible.

This doc compares every data source used in ESO Build Genius to that authority.

---

## 1. Where the “Zenimax ESO API” lives

| Source | Publisher | What it is | URL / location |
|--------|-----------|------------|----------------|
| **API patch notes** | Zenimax (via ESOUI) | Addon API changes for the patch | ESOUI forum attachment per patch (see [PATCH_SOURCES.md](PATCH_SOURCES.md)) |
| **API TXT documentation** | Zenimax (via ESOUI) | Full addon API text dump (Lua globals, functions, signatures) | ESOUI forum attachment per patch |
| **Game client files** | Zenimax (ESO install) | MNF/DAT/LANG etc. – raw game data | Local install; extract with EsoExtractData / uesp-esoapps |
| **UESP ESO API (mirror)** | UESP community | Build-tagged Lua API derived from game files / parseGlobals | https://esoapi.uesp.net/index.html, https://esodata.uesp.net |

The **authoritative** references are the Zenimax API documents (API TXT + patch notes) and the game folder contents. The UESP mirror is useful for version mapping and names but is not the official publisher.

---

## 2. Authority hierarchy (summary)

| Priority | Source | Use for |
|----------|--------|--------|
| **1 – Authoritative** | Zenimax API TXT + API patch notes; or game client extraction | API version, build labelling, validation of IDs/names; full catalogs if extracted from client |
| **2 – Primary when API doesn’t provide content** | Addon export (your addon calling official API in-game) | Sets, items, skills, buffs, food, potions – as exposed to addons (e.g. GetItemLinkSetInfo, GetAbilityName) |
| **3 – Community / datamined** | UESP ESO Log, UESP wiki, xlsx, seeds | Fill gaps when we don’t have addon or client extract; validate against API/authoritative where possible |

---

## 3. Per–data-domain comparison

What we store and where we get it today vs what the Zenimax API / game files provide.

### 3.1 Item sets (set_summary, set_bonuses, set_item_slots)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Set list, IDs, names, bonus text, slots | **UESP ESO Log** `exportJson.php?table=setSummary` | **Game files:** yes (datamined; addons can use GetItemLinkSetInfo etc.). **API TXT:** function names only, not full set catalog. | UESP setSummary is community datamining of the same data. **Authoritative** would be addon export (in-game API) or client extraction. Prefer validating set IDs and names against API TXT / addon if available. |

### 3.2 Set → buff mapping (buff_grants_set_bonus)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Which set bonus grants which buff | **Derived** by parsing set_bonus_desc (from UESP setSummary) | **Game files:** buff and set data exist; no single “set grants buff” table exposed in API TXT. Addons can infer from tooltips/links. | Parsed from same set text that addon/game could use. **Authoritative** would be client or addon-derived mapping. Keep parsing; optionally validate buff names against API/globals if present in API TXT. |

### 3.3 Skills and coefficients (skills, coefficient_json)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Ability IDs, names, skill lines, cost, duration, cast time | **UESP ESO Log** `skillCoef` / `minedSkills` | **Game files:** ability/skill data present. **API TXT:** GetAbilityName, GetAbilityDescription etc. – names/IDs discoverable via addon. | UESP is datamined. **Authoritative** = addon export (GetAbility*) or client extraction. Use API TXT / addon to validate ability IDs and names when possible. |
| Damage/heal coefficients (formula: type, a, b, c, R, avg) | **UESP ESO Log** `skillCoef` | **Game files:** yes (used for tooltips/combat). **API TXT:** no – formulae not exposed to addons. | Coefficients are **not** in the addon API; only in client or community regression (e.g. UESP viewSkillCoef). Keep UESP skillCoef as source; document that it is community regression, not from Zenimax API. |

### 3.4 Skill lines (skill_lines, link skills → lines)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Class/weapon/guild line IDs and names | **Seeds** (07, 09) + **UESP ESO Log** playerSkills / **xlsx** (link_skills_to_skill_lines) | **Game files:** yes. **API TXT:** skill line related functions if documented. Addons: GetSkillLineInfo etc. | **Authoritative** = game or addon. Use verify_skill_lines_esolog / link_skill_lines_from_esolog to align with ESO Log; treat API/addon as source of truth for line IDs when available. |

### 3.5 Buffs (buffs, buff_grants)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Buff IDs, names, effect type, magnitude | **Seeds** (07, 07b) – hand-curated from wiki/community | **Game files:** yes. **API TXT:** buff-related globals/functions if any (e.g. effect names). | No Zenimax-published buff catalog in API TXT. **Authoritative** = client or addon. Keep seed; validate names against API TXT if buff constants/strings appear there. |

### 3.6 Foods and potions (foods, potions)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Food/potion IDs, names, duration, effects | **UESP wiki** (fetch_foods_uesp, fetch_potions_uesp) → JSON → ingest_food_potions | **Game files:** yes (provisioning data). **API TXT:** GetItemLink* etc. – addon can export. | Wiki is community. **Authoritative** = addon export or client extraction. Use API/addon to validate IDs and names when possible. |

### 3.7 Mundus stones (mundus)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Mundus IDs, names, effects | **Seed** (10_seed_mundus_food_potions.sql) from UESP wiki | **Game files:** yes. **API TXT:** mundus-related functions if documented. | Same as foods/potions – **authoritative** = game or addon. Seed is acceptable until addon/client source is used. |

### 3.8 Race effects (race_effects)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Race passives (name, effect text, magnitude) | **Seed** (13_seed_race_effects.sql) from UESP wiki race pages | **Game files:** yes. **API TXT:** no full catalog. Addons can read tooltips. | **Authoritative** = client or addon. Keep seed; validate passive names against API if present. |

### 3.9 Traits, glyphs, weapon poisons (traits, glyphs, weapon_poisons)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Trait/glyph/poison IDs and names | **Seed** (12_seed_traits_glyphs_poisons.sql) | **Game files:** yes. **API TXT:** item/trait functions. | **Authoritative** = game or addon. Seed is placeholder until addon/client export. |

### 3.10 Stat reference and weapon stats (stat_modifier_reference, weapon_type_stats)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Stat caps, weapon type bonuses | **xlsx** (Standalone Damage Modifiers Calculator) + **seed** (14 weapon_type_stats) | **Game files:** yes (combat/stat logic). **API TXT:** not as structured tables. | **Authoritative** = client. xlsx/seed are community; validate values against client or addon when possible. |

### 3.11 Trials, bosses, trash (trials, trial_bosses, trial_trash_packs)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Trial/boss names, pack structure | **Seeds** (16, 18) from UESP wiki | **Game files:** zone/encounter data may exist. **API TXT:** not a catalog. | **Authoritative** = client or internal encounter data. Wiki/seed are non-authoritative; document and replace when we have a proper source. |

### 3.12 Scribing (scribe_effects, skill_scribe_compatibility)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Scribe effect slots and names | **UESP** [Online:Scribing](https://en.uesp.net/wiki/Online:Scribing) via `fetch_scribe_effects_uesp.py` + `ingest_scribe_effects.py` (67 scripts: 21 Focus, 20 Signature, 26 Affix). Seed 05b has no INSERTs; catalog is populated by ingest. | **Game files:** yes (Scribing system). **API TXT:** scribing-related functions if added. | **Authoritative** = game or addon (e.g. esoapi.uesp.net ingame/crafting/scribingdata.lua). UESP wiki is the current source for the full catalog until game/API data is used. |

### 3.13 Game build and API version (game_builds.api_version)

| Aspect | Our current source | In Zenimax API / game files? | Comparison / recommendation |
|--------|--------------------|------------------------------|-----------------------------|
| Build label, API version | **Manual** (create_db / seed 07) + optional UESP esoapi.uesp.net version index | **Zenimax:** API patch notes and API TXT list or imply API version for the patch. **In-game:** GetAPIVersion(). | **Authoritative** = API TXT / patch notes or addon GetAPIVersion(). Use Zenimax docs (or UESP mirror) to set game_builds.label and api_version. |

---

## 4. Summary table: source vs authority

| Data domain | Our current source | Provided by Zenimax API? | Provided by game files? | Recommendation |
|-------------|--------------------|---------------------------|--------------------------|----------------|
| Set catalog (names, bonuses, slots) | UESP setSummary | No (only addon callables) | Yes (datamined) | Prefer addon export or client extract; validate IDs/names with API |
| Set → buff mapping | Parsed from set bonus text | No | Inferrable | Keep; validate buff names with API if present |
| Skills (IDs, names, metadata) | UESP skillCoef/minedSkills | IDs/names via addon API | Yes | Prefer addon export or client; validate with API TXT |
| Skill coefficients (formulae) | UESP skillCoef | **No** (not in addon API) | Yes (in client) | Keep UESP; document as non-API; client extract would be authoritative |
| Skill lines | Seeds + UESP playerSkills + xlsx | Via addon (e.g. GetSkillLineInfo) | Yes | Align with addon/client; use API for validation |
| Buffs | Seeds (07, 07b) | Not as catalog | Yes | Addon/client for authority; validate names with API |
| Foods / potions | UESP wiki → JSON | Via addon GetItemLink* | Yes | Prefer addon export or client |
| Mundus / race effects / traits / glyphs / poisons | Seeds (10, 12, 13, 14) | Partial (addon callables) | Yes | Prefer addon or client export when available |
| Stat / weapon reference | xlsx + seed | No | Yes | Prefer client; xlsx is community |
| Trials / bosses / trash | Seeds + wiki | No | Possibly in client | Replace with client or official source when available |
| Scribe effects | UESP Online:Scribing (fetch + ingest; 67 scripts) | When documented | Yes | Authoritative = game/addon; UESP used for full catalog until then |
| Build / API version | Manual + UESP version index | **Yes** (API TXT, patch notes) | GetAPIVersion() | Use Zenimax API TXT and patch notes as authority |

---

## 5. Recommended next steps

1. **Use Zenimax API TXT and API patch notes** (see [PATCH_SOURCES.md](PATCH_SOURCES.md)) to set and validate `game_builds.label` and `game_builds.api_version` per patch.
2. **Add an addon-based exporter** that calls in-game API (GetItemLinkSetInfo, GetAbilityName, GetSkillLineInfo, etc.) and exports sets, skills, skill lines, foods, potions, mundus, and optionally buff names to JSON; treat that as **primary** for those domains where the API TXT does not publish full catalogs.
3. **Keep UESP ESO Log and wiki** for skill coefficients (not in addon API), for set/skill catalogs until addon export exists, and for validation.
4. **Document in each ingest script** whether the source is authoritative (Zenimax/game) or community (UESP/wiki/xlsx), and add a note in [DATA_SOURCES.md](DATA_SOURCES.md) pointing to this comparison.

This keeps the pipeline aligned with the rule: **Zenimax ESO API (and game folders when extracted) are authoritative; all other sources are compared and validated against them.**
