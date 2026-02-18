# ESO Build Genius – UI Design

This document describes the application UI: build form, equipment/skill layout, and the live **Advisor** that recommends sets, skills, and passives as the user makes choices.

---

## 1. Build form (user inputs)

All controls are bound to the current “build” (e.g. a `recommended_builds` row or in-memory draft). Selections drive Advisor recommendations immediately.

| Field | Control | Source / notes |
|-------|---------|----------------|
| **Class** | Combo box | `classes` (Dragonknight, Sorcerer, Nightblade, Templar, Warden, Necromancer, Arcanist). *Subclassing:* tabled for later; future design may add “Replace class line 2 / 3” with another class’s line. |
| **Race** | Combo box | `races` (Altmer, Argonian, Bosmer, Breton, Dunmer, Imperial, Khajiit, Nord, Orc, Redguard). |
| **Role** | Combo box | `roles`: Damage Dealer, Healer, Tank. **Support DD:** add a secondary control (e.g. checkbox “Support DD / Buff Bitch”) so the user can indicate a DD focused on group buffs/debuffs; map to `role_id = support_dd` or a role + flag. Display labels can be “Damage Dealer”, “Healer”, “Tank”, “Support DD” with the vernacular note in tooltip or help. |
| **Mundus** | Combo box | `mundus_stones` for current game build. One selection. |
| **Food / Drink** | Combo box (or searchable list) | `foods` for current game build. |
| **Potions** | Combo box (or searchable list) | `potions` for current game build. |

**Data binding:** Class → `recommended_builds.class_id`, Race → `race_id`, Role → `role_id` (and support-DD flag if separate), Mundus → `mundus_id`, Food → `food_id`, Potion → `potion_id`.

---

## 2. Equipment slot layout (visual)

A clear visual of **where** set pieces go. Each slot shows the currently chosen set (and optionally piece type, e.g. “Light Head”). Slots are grouped as below. Naming matches ESO; “Arms” = Hands.

**Body (7 slots)**  
Head, Shoulders, Chest, **Hands** (Arms), Waist, Legs, Feet.

**Jewelry (3 slots)**  
Necklace, Ring 1, Ring 2.

**Weapons (4 slots)**  
Front Bar: Main Hand, Off Hand.  
Back Bar: Main Hand, Off Hand.

Total: **14 slots**. Each slot is bound to `recommended_build_equipment`: `(recommended_build_id, slot_id, set_id)`. The user (or Advisor) picks a **set** per slot; piece type (e.g. head vs feet) can be implied by slot or chosen separately if the UI supports it.

**Schema:** `equipment_slots` includes 14 slots (01_schema: 1–11; 08_equipment_slots_jewelry: 12 neck, 13 ring1, 14 ring2). `recommended_build_equipment` and set slot rules use these IDs.

---

## 3. Advisor (live recommendations)

The **Advisor** is a panel (or sections) that updates as the user changes the form or slots. It does not wait for “Submit”; it reacts to Class, Race, Role, Mundus, Food, Potions, and current equipment/skill choices.

### 3.1 What the Advisor recommends

1. **Equipment sets**  
   Suggests which sets to wear in which slots (body, jewelry, weapons), respecting:
   - Slot rules (e.g. monster vs body, mythic count).
   - **Buff/debuff coverage (self-buffs first):** avoid sets that only duplicate buffs already provided by this build (slotted skills, passives, other equipped sets). Use `buff_coverage` and `buff_grants_set_bonus` / `buff_grants`. Implemented in `scripts/recommendations.py` and `recommend_sets.py`. Team composition (external buffs from healer/tank) is a later phase.
   - Role and class (e.g. healer vs DD sets).

2. **Skills and passives**  
   - Which **skill lines** to use (class + weapon + guild etc.). For class, subclassing can be reflected later (which 3 class lines).
   - Which **passives** to take within those lines (from `skill_line_passives`).
   - A concrete **bar layout**: **12 skills** total:
     - **Front bar:** 5 skills + 1 ultimate (slots 1–6).
     - **Back bar:** 5 skills + 1 ultimate (slots 7–12).  
   Stored in `recommended_build_scribed_skills` (and/or a dedicated bar layout table if we split “which ability” from “which scribed variant”). The Advisor suggests ability_id (and optionally scribe effect ids) per bar slot.

3. **Weapons**  
   Recommendations include **which weapon types** (and thus which sets) go on front main/off and back main/off (e.g. infer from `recommended_builds.weapon_type` and set slots). The same 14-slot visual shows the chosen set per weapon slot.

### 3.2 Example flow

- User selects **Templar**, **Argonian**, **Healer** (and optionally Support DD off).
- Advisor reacts: suggests healer-oriented sets (e.g. SPC, PA, etc.), Mundus/Food/Potions suited to healer, and a **12-skill bar**: front bar (e.g. Combat Prayer, Illustrious Healing, … + Ultimate), back bar (e.g. Elemental Blockade, … + Ultimate), plus which passives to take.
- As the user picks or changes a set in a slot, the Advisor can re-run buff coverage and warn or adjust (e.g. “Kinras 5pc is redundant with Combat Prayer for Minor Berserk”).

### 3.3 Implementation notes

- **Inputs to the Advisor:** `game_build_id`, `class_id`, `race_id`, `role_id`, support_DD flag, `mundus_id`, `food_id`, `potion_id`, current `recommended_build_equipment` (or draft), current bar layout if any.
- **Outputs:** Suggested set per slot (or a short list per slot), suggested 12 skills (front 6 + back 6), suggested passives, and optional short text (e.g. “Minor Berserk covered by Combat Prayer; avoid Kinras 5pc for that reason”).
- Recommendations can be “apply” actions (user clicks to fill a slot or the bar) or copyable text; the form and slot visual remain the single source of truth for what the build is.

---

## 4. Screen layout (conceptual)

- **Left (or top):** Build form (Class, Race, Role, Support DD, Mundus, Food, Potions).
- **Centre:** Equipment slot grid (14 slots), grouped as Body / Jewelry / Front Bar / Back Bar, each showing selected set (and optionally piece type).
- **Right (or below):** Advisor panel: equipment suggestions, then skill/passive suggestions, then the 12-skill bar (e.g. two rows of 6), then any warnings (e.g. duplicate buff).
- Optional: separate tabs or sections for “Summary”, “Stats”, “Buffs covered”, etc.

---

## 5. Data and schema alignment

| UI concept | Schema / table |
|------------|----------------|
| Class, Race, Role | `recommended_builds.class_id`, `race_id`, `role_id`; `roles` includes `support_dd`. |
| Mundus, Food, Potion | `recommended_builds.mundus_id`, `food_id`, `potion_id`; `mundus_stones`, `foods`, `potions`. |
| Set per slot | `recommended_build_equipment` (recommended_build_id, slot_id, set_id); `equipment_slots`. |
| 12-skill bar | `recommended_build_scribed_skills` (bar_slot_ord 1–12, ability_id, scribe_effect_id_1/2/3). |
| Which class lines | `recommended_build_class_lines` (slot_ord 1–3, skill_line_id); subclassing. |
| Advisor logic | Buff coverage (`buff_grants`, `buff_grants_set_bonus`), set rules, role/class filters. |

---

## 6. Design decisions tabled

- **Subclassing in the UI:** Where to choose “replace class line 2/3” (e.g. extra combo boxes, modal, or “Advanced” section). Leave for a later iteration.
- **Support DD:** Final control (combo sub-option vs checkbox vs separate role entry) and whether to store as `role_id = support_dd` only or role + flag.
- **Jewelry slots:** Added in schema 08 (`neck`, `ring1`, `ring2`). UI should use all 14 slots.
- **Scribing in the bar:** Whether each of the 12 bar slots shows scribed variant (base + up to 3 effects) in the first version or later.

This gives a single reference for the form, slot layout, and Advisor behavior and ties them to the existing schema and recommendation rules (including buff de-duplication and future subclassing).
