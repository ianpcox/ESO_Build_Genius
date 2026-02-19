# ESO Build Genius – Design Plan

## 1. Scope and goals

- **Platform:** PC only (no Xbox/PlayStation).
- **Content:** PvE only. No Battlegrounds, Cyrodiil, Imperial City, or Duelling.
- **First focus:** 12-person Trials. Later: 4-person Dungeons/Arenas, then solo arenas.
- **Deliverable:** Min-maxing tool that recommends optimal **builds** (race, equipment, food, potions, mundus) per **role** (healer, tank, DD, support DD) per **class**, for Trials, with the ability to adapt per trial or boss later.

Builds are **class-specific** and can use:
- **Class skill lines:** Each class has exactly three class skill lines (e.g. Necromancer: Grave Lord, Bone Tyrant, Living Death). **Subclassing** allows a character to *replace* up to two of their base class lines with class skill lines from up to two other classes. Example: a Necromancer keeps "Grave Lord", replaces "Bone Tyrant" with Nightblade's "Assassination", and "Living Death" with Arcanist's "Herald of the Tome". So the character still has three class skill lines in total; at most two of them come from other classes.
- Weapon, guild, world (e.g. Vampire, Werewolf), and **scribed** skill lines (unchanged by subclassing). **Scribing** lets players take a base skill and add up to three additional effects (e.g. Focus, Signature, Affix scripts), which greatly increases build diversity (see 2.4). **Optimal is complex:** subclassing and scribing multiply the build space; optimization may need to constrain or sample over these dimensions.

The main challenges are:
1. **Data:** Where to get accurate, up-to-date game data with minimal “recognition lag” after patches.
2. **Optimization:** Combinatoric search over sets, slots, mundus, food, potions, skills/rotations, **subclass choices**, and **scribed skill variants**, with correct damage/healing/survival formulas. Scribing alone adds many combinations per bar slot (base + 0–3 effects), so "optimal" recommendations may need to focus on a subset of scribed variants or use heuristics.

---

## 2. Build components (summary)

| Component   | Examples / notes |
|------------|-------------------|
| Race       | Affects stats and passives (e.g. sustain, crit, max resource). |
| Equipment  | 12 body/weapon slots; typically 2× 5-piece sets + 1 monster (2pc) + 1 mythic (1pc) or 2× 5-piece + monster; traits, enchants, weight. |
| Food       | Max stats, recovery, hybrid; duration and magnitude. |
| Potions    | Combat buffs (e.g. Crit, Weapon/Spell Damage), resource restore. |
| Mundus     | One per character (e.g. Thief, Shadow, Warrior). |
| Skills     | (Later) Bar layout and rotation for DPS/heal/tank; support DD focuses (e.g. Stagger uptime, Crystal Weapon armour debuff). |

Roles: **Healer**, **Tank**, **DD** (damage dealer), **Support DD** (e.g. DK Stagger, Sorc Crystal Weapon for armour debuff).

### 2.1 Skill lines and class lines

- **Skill lines** are first-class entities per game build: *class*, *weapon*, *guild*, *world*, *scribed*. Each has a type and a name; class lines also reference a class (e.g. "Grave Lord" belongs to Necromancer).
- **Class skill lines:** Every class has exactly three class skill lines. Skills (abilities) belong to a skill line; `skills.skill_line_id` references `skill_lines`. Builds choose which three class lines they use via **subclassing** (see above): base class + up to two replacements from other classes.
- **Passives:** Each skill line has passives (stored in `skill_line_passives`). Passives can grant buffs/debuffs; see below.

### 2.2 Buffs and debuffs (standalone, linked to sources)

- A **standalone buff/debuff** table (`buffs`) holds effect name, type, magnitude, duration. **Buffs are linked to their sources** via `buff_grants` (abilities and skill-line passives) and **`buff_grants_set_bonus` (06)** (set bonuses: which set + num_pieces grants which buff). So we can answer "what grants Minor Berserk?" → e.g. Combat Prayer (ability), Kinras's Wrath 5pc (set bonus), etc.
- Target granularity (see 2.3) applies where a buff or effect is conditional on target type.

### 2.5 Buff/debuff coverage – avoid duplicates when optimizing

- **Same buff from multiple sources is redundant** for optimization. Example: if a healer runs **Combat Prayer** and maintains high uptime on **Minor Berserk**, then adding **Kinras's Wrath** (5pc grants Minor Berserk) does not add a new buff—it doubles up. The optimizer should either **exclude** or **deprioritize** set bonuses (and other sources) that only provide buffs already covered by the build’s skills and passives at expected uptime.
- **Implementation:** For a candidate build, compute "buff coverage" from (1) slotted abilities, (2) passives from chosen skill lines, and (3) equipped set bonuses (using `buff_grants` and `buff_grants_set_bonus`). When evaluating an extra set or slot choice, if it would add a buff_id that is already in the coverage set, treat it as redundant for that buff (unless e.g. backup uptime is desired). Prefer sets that add **new** buffs or other value (e.g. raw stats) over sets that only duplicate existing buffs.

### 2.3 Target granularity

- Many effects vary by **target type**: e.g. vs. Undead, vs. Daedra, vs. Humanoid, Beast, Construct, Player. The schema includes `target_types` (lookup) and `skill_target_bonus` (which skills get a bonus or different effect vs. which target types). This supports correct DPS/simulation when the trial or boss has a specific type (e.g. Undead).

### 2.4 Scribing

- **Scribing** allows players to take a **base skill** (from the Scribing skill line or eligible abilities) and add **up to 3 additional effects** on top of it (e.g. Focus script, Signature script, Affix script). Each effect comes from a catalog (damage type, DoT, Major/Minor buff/debuff, etc.). The result is a customized skill that still uses the base’s core behavior but with extra effects.
- This creates **many more build possibilities**: the same bar slot can be filled with "base Skill A" or "base Skill A + effect 1", "base Skill A + effect 1 + effect 2", etc., up to three effects. What counts as "optimal" depends on role, trial, and preferences (e.g. max DPS vs. survivability vs. group buffs), and the combinatorics are large.
- **Schema (05_scribing):** `scribe_effect_slots` (lookup: e.g. Focus, Signature, Affix), `scribe_effects` (catalog of add-on effects per game build, per slot), optional `skill_scribe_compatibility` (which effects can apply to which base skills), and `recommended_build_scribed_skills` (per build: bar slot, base ability_id, and 0–3 scribe_effect_ids). Optimization and recommendations should account for scribed variants (e.g. by constraining to popular or high-impact combinations, or by sampling).

---

## 3. Data sources (prioritised by recognition lag)

Recognition lag = delay between a game patch and your data reflecting it. Sources below are ordered from **lowest to highest** expected lag.

### 3.1 Lowest lag – you control the update

| Source | What it gives | How to use | Lag |
|--------|----------------|------------|-----|
| **In-game addon export** | Items, sets, skills, buffs, tooltips as the client sees them | Run an addon after each patch that dumps to JSON/Lua (SavedVariables or file export). Parse in your pipeline. | **None** if you run post-patch. |
| **EsoExtractData** | Raw data from ESO `.mnf`/`.dat` client files | Extract and parse; highest fidelity but format is reverse-engineered, large (100GB+ full export). | **None** once you automate extraction per patch. |

**Recommendation:** Use an **addon-based exporter** as the primary source of truth. Options:
- **ESO Data Dumper** ([GitHub: sevenseacat/eso_data_dumper](https://github.com/sevenseacat/eso_data_dumper)) – dumps achievements, dyes; extend or copy pattern for sets/skills.
- **Item Set Dumper** ([ESOUI](https://www.esoui.com/downloads/info3488-ItemSetDumper.html)) – dumps item sets to SavedVariables.
- **Custom addon** – call ESO’s Lua API (e.g. `GetItemLinkSetInfo`, set collection iteration, skill/ability APIs) and write structured JSON/Lua to SavedVariables; a small external script can move files into your repo or DB.

This gives you **versioned snapshots per game build** with no dependency on third-party sites updating.

### 3.2 Low lag – UESP (datamined / extracted from client)

UESP provides several sites, all tied to game builds or player uploads. They are among the best **external** sources.

| Source | URL | What it gives | Update mechanism | Lag |
|--------|-----|----------------|-------------------|-----|
| **ESO API (Lua globals)** | [esoapi.uesp.net](https://esoapi.uesp.net/) / [esodata.uesp.net](https://esodata.uesp.net/) | Lua API surface: 139k+ functions, 587k+ globals, API diffs between versions. | Build-tagged (e.g. v101047 = 2025-08-29). New version when someone runs extractor after patch. | **Low** – usually within days of patch; [version index](https://esoapi.uesp.net/index.html) available. |
| **Skill coefficients** | [esoitem.uesp.net/viewSkillCoef.php](https://esoitem.uesp.net/viewSkillCoef.php) | ~7k skills with **damage/heal equations** (MaxStat, MaxPower, ratios, ticks, etc.). Essential for DPS/heal math. | Community regression/datamining. | **Low** – maintained with patches; R² ~0.9999 for tooltip fit. |
| **ESO Log (datamined records)** | [esolog.uesp.net](https://esolog.uesp.net/viewlog.php) | setSummary, minedItem, minedSkills, etc. (e.g. 142k+ set summaries, 173M+ item records). | **uespLog** addon: players upload SavedVariables to UESP; DB updated from submissions. | **Low–medium** – depends on player submissions after each patch. |
| **ESO Log record types** | Same site, `?record=...` | e.g. `setSummary`, `minedItem`, `minedSkills`, `minedSkillLines`. | Same. | Same. |

Use **esoapi.uesp.net** for:
- Mapping game build ↔ your data version.
- Discovering/validating API names for your addon exporter (e.g. set/ability IDs).

Use **esoitem.uesp.net/viewSkillCoef.php** for:
- All **skill coefficients** needed for damage and healing formulas in the optimizer.

Use **esolog.uesp.net** for:
- **Set bonuses** and item metadata (if you don’t yet have addon dumps).
- Cross-checking your addon output.

### 3.3 Medium lag – community APIs and libraries

| Source | What it gives | Lag |
|--------|----------------|-----|
| **ESO Sets API** | [eso-sets.herokuapp.com](https://eso-sets.herokuapp.com) – REST and GraphQL (sets by name, bonuses, type). [GitHub: JimmyMcBride/eso-sets-api](https://github.com/JimmyMcBride/eso-sets-api). | **Medium** – likely manual or periodic scrape; check repo/owner for update policy. |
| **LibSets** (Baertram) | [GitHub: Baertram/LibSets](https://github.com/Baertram/LibSets) – Lua tables + API for set data; used by many addons. | **Medium** – maintainer updates per patch; good for addon-side use or parsing Lua into your DB. |
| **ESO-Database game-data** | [game-data.eso-database.com](https://game-data.eso-database.com) – API for addon authors (e.g. chests, nodes); may expand. | **Medium** – crowd-sourced via their addon. |

Use these as **secondary or fallback** once you have addon export or UESP as primary.

### 3.4 Reference only – high lag

| Source | Use |
|--------|-----|
| **ESO-Hub** ([eso-hub.com](https://eso-hub.com)) | Build ideas, set lists, guides. Not recommended as **primary** data – human-curated, lag after patches. |
| **Official patch notes** | [forums.elderscrollsonline.com/.../patch-notes](https://forums.elderscrollsonline.com/en/categories/patch-notes) – **authoritative for “what changed”**, not for full DB. Use for versioning and changelog (e.g. “this build is for Update 48”). |

---

## 4. Recommended data strategy

1. **Primary (authoritative):**
   - **Addon exporter** run by you after each patch: dump sets, items, skills (and optionally buffs, mundus, food, potions) to JSON. Tag every snapshot with **game build** (e.g. from `GetAPIVersion()` or patch notes).
   - **Skill coefficients:** Ingest from **esoitem.uesp.net** (scrape or use if they add an API) and store by build/date; or replicate their regression from raw tooltips if you have them via addon.

2. **Secondary / validation:**
   - **UESP ESO Log** setSummary and minedItem for sets/items.
   - **esoapi.uesp.net** version index to map build ↔ API version and detect new patches.

3. **Versioning:**
   - Store all game data keyed by **build id** or **patch label** (e.g. Update 48). When patch notes show a new incremental, re-run addon (and optionally re-scrape UESP) and create a new snapshot. This keeps “optimal build” outputs tied to a specific game state.

4. **Patch notes:**
   - Parse or manually note major balance changes (set/ability/skill line changes) to know when to re-run optimizer and invalidate caches.

---

## 5. Data model (high level)

- **GameBuild** – id, label (e.g. “Update 48”), date, source snapshot id.
- **Race** – id, name, passives (stats, regen, etc.); can be from addon or UESP.
- **ItemSet** – id, name, type (crafted, dungeon, trial, mythic, monster, etc.), piece count, bonuses by numEquipped (2–5, or 1 for mythic, 2 for monster). Optional: source location.
- **Item** – id, set id, slot, trait, armour/weapon type, level (e.g. CP 160).
- **Skill / Ability** – id, name, skill line, class (if any), mechanic (Magicka/Stamina/Ultimate etc.), **coefficients** (from esoitem.uesp or addon): equation, ratio, duration, tick, type (Direct, DoT, Heal, etc.).
- **Buff / Debuff** – id, name, effect (e.g. Major Brutality, Minor Brittle), magnitude/duration if fixed.
- **Mundus** – id, name, effect (e.g. crit, weapon damage).
- **Food / Drink** – id, name, effects (max stat, recovery, etc.), duration.
- **Potion** – id, name, effects (buffs, restore), duration, cooldown.
- **Build** – gameBuildId, class, role, raceId, mundusId, foodId, potionId, equipment (slot → item/set piece), optional skillBar (later). Constraints: 1 mythic, 2× 5-piece + 1× 2-piece monster (or equivalent), slot rules.
- **Trial** (later) – id, name; **TrialBoss** – id, trialId, name; optional per-boss overrides (e.g. different pen or survivability).

All of the above should be **versioned by GameBuild** so the optimizer always runs against one consistent snapshot.

---

## 6. Optimization and combinatorics

### 6.1 Objective

- **DD / Support DD:** Maximise effective DPS (or group utility metric for support DD), subject to sustain and survivability constraints.
- **Healer:** Maximise effective HPS and prioritise buff and debuff uptimes (group buffs/debuffs from skills and sets), subject to sustain.
- **Tank:** Maximise survivability (effective health, mitigation), taunt uptime, and prioritise buff and debuff uptimes (group buffs/debuffs), subject to sustain.

For DD, damage is driven by:
- **Skill coefficients** (from esoitem.uesp) × (MaxStat, MaxPower) with correct ratio (e.g. 10.5).
- **Buffs:** Major/Minor Brutality/Sorcery, Crit, Force, etc., from sets, potions, food, mundus, skills.
- **Debuffs on target:** Major/Minor Breach, Brittle, etc. (support DD builds may maximise these).
- **Armour mitigation** (target armour, pen).
- **Critical chance and critical damage.**

So the optimizer needs: set bonuses (flat stats, % damage, procs), mundus, food, potions, and race passives merged into one “stat block” and then fed into a **damage formula** that uses skill coefficients.

### 6.2 Combinatoric structure

- **Discrete choices:** Race, mundus, food, potion.
- **Equipment:** Which two 5-piece sets + which monster set + which mythic (or no mythic); which slot gets which set piece (body vs weapon); traits and enchants. Slot layout is constrained (e.g. 7 body + 2× 2H or 2× DW etc.).
- **Later:** Skill bar and rotation (priority order, DoT refresh, spammable) for full DPS simulation.

Approach:
1. **Reduce search space:** Restrict to “meta” or “trial-viable” sets per role (from community or from your own filters) to avoid enumerating every combination.
2. **Objective function:** For each candidate build (race + gear + food + potion + mundus), compute derived stats and then **expected damage per second** (or survivability / HPS) using skill coefficients and buff stacking rules. Use a **single representative rotation** (e.g. 1–2 DoTs + spammable + ultimate) or a small set of rotations per class.
3. **Solver:** Greedy, beam search, or integer/constraint programming over set choices and slot assignment; or brute over a small “allowed sets” list. No need for full MIP initially.

### 6.3 Constraints

- Exactly 12 equipment slots; at most 1 mythic; at most 2 full 5-piece sets; monster 2-piece only on head/shoulder (or 1-piece + 1 from another set in some metas).
- Race/class/role compatibility (e.g. only certain classes for “support DD” with Stagger/Crystal Weapon).
- Sustain: max resource and recovery (from food, sets, potions) above a threshold so the build is playable.

---

## 7. Pipeline (ingest → normalize → optimize → output)

1. **Ingest**
   - Run addon after patch → export JSON.
   - Optionally scrape UESP (skill coef, setSummary) and store by build.
   - Record game build id and patch label (from patch notes or API version).

2. **Normalize**
   - Map raw set/item/skill/buff IDs to your canonical schema.
   - Attach skill coefficients to abilities; resolve set bonuses to structured effects (flat stats, % damage, procs).
   - Build “stat block” calculator: given (race, sets, food, potion, mundus) → (WD/SD, crit, max stats, recovery, pen, etc.).

3. **Optimize**
   - For each (gameBuild, class, role) – optionally (trial, boss):
     - Generate or enumerate candidate builds (within “allowed” sets and slot rules).
     - Score each build (DPS / HPS / survivability).
     - Return top N builds; optionally store in DB.

4. **Output**
   - Per class/role: “Optimal Trials build” (and later per trial/boss).
   - Expose via UI or API; optionally “diff” vs previous build when patch changes.

---

## 8. Implementation phases

| Phase | Focus | Deliverable |
|-------|--------|-------------|
| **1 – Data** | Addon exporter (or Item Set Dumper + custom) for sets/items; ingest skill coef from UESP; store by build. | Versioned DB (or JSON snapshots) of sets, items, skills (with coef), mundus, food, potions, races. |
| **2 – Model** | Stat block calculator; damage formula using skill coefficients; constraints (slots, 1 mythic, 2×5+2). | For any (race, sets, food, potion, mundus) → derived stats and single-target DPS estimate. |
| **3 – Optimizer** | Restricted set list per role; combinatoric search (greedy/beam/CP); objective = DPS for DD. | Top builds per (class, role) for Trials, PC PvE. |
| **4 – Support DD / Healer / Tank** | Separate objectives and constraints; support DD utility (e.g. Stagger, Crystal Weapon). | Optimal builds for support DD, healer, tank. |
| **5 – Trials and bosses** | Optional per-trial or per-boss overrides (e.g. more pen, more survivability). | Build recommendations per trial/boss. |
| **6 – 4-person and solo** | Dungeons, arenas, solo; adjust constraints/objectives. | Extended scope. |

---

## 9. Tech stack

**Recommended: Python + SQL (SQLite to start).**

| Need | Why Python + SQL fits |
|------|----------------------|
| **Optimization** | Numeric and combinatoric work (stat blocks, damage formula, set search) is standard in Python: NumPy, SciPy, Pandas, and optionally PuLP/OR-Tools for constraint search. Node can do it but has a weaker numeric/optimization ecosystem. |
| **Data wrangling** | Ingesting addon JSON, parsing UESP tables (e.g. skill coefficients), normalizing set bonuses = tabular and string handling. Pandas + Python is a natural fit; SQL gives versioned, queryable storage per build. |
| **Storage** | Relational model (GameBuild, ItemSet, Skill, Buff, etc.) and versioning by `build_id` map cleanly to SQL. SQLite is enough for one developer and single-machine runs; move to PostgreSQL if you need remote or concurrent access later. |
| **Ingestion** | `requests` + BeautifulSoup or lxml for UESP; `json` (and if needed a small Lua parser) for addon output. Simple scripts or a small CLI (e.g. `ingest`, `optimize`) are straightforward. |
| **API later** | If you expose “best build for Arcanist DD” via HTTP, FastAPI or Flask is minimal and works well with the same Python code and DB. |

**Alternatives:** Node + JSON is viable if you prefer a single language and don’t need heavy optimization libraries; you’d store versioned JSON snapshots and use lodash/plain JS for transforms. Given your strength in Python/SQL and the optimization-heavy nature of the project, Python + SQL is the better fit and will iterate faster.

**Concrete choice:** Python 3.11+; SQLite (file per project or one DB); Pandas for transforms; NumPy for damage formula; optional FastAPI for a small REST API. Add PuLP or OR-Tools in Phase 3 when you implement the combinatoric optimizer.

---

## 10. References

- [UESP ESO API (versions)](https://esoapi.uesp.net/index.html)
- [UESP ESO Skill Coefficients](https://esoitem.uesp.net/viewSkillCoef.php)
- [UESP ESO Log Data Viewer](https://esolog.uesp.net/viewlog.php)
- [ESO Sets API (REST/GraphQL)](https://eso-sets.herokuapp.com/) – [GitHub](https://github.com/JimmyMcBride/eso-sets-api)
- [ESO Data Dumper addon](https://github.com/sevenseacat/eso_data_dumper)
- [LibSets (Baertram)](https://github.com/Baertram/LibSets)
- [ESO-Hub](https://eso-hub.com) – Build Editor, sets, guides (reference)
- [Official ESO Patch Notes](https://forums.elderscrollsonline.com/en/categories/patch-notes)
- [ESO damage guide (forum)](https://forums.elderscrollsonline.com/en/discussion/422268/a-comprehensive-guide-on-damage-dealing-in-elder-scrolls-online) – formula context

---

*Document version: 1.1. Scope: Trials, PC, PvE; data sources prioritised by patch lag; tech stack: Python + SQL; optimization and pipeline outlined for later implementation.*
