# Combat timing and damage simulation

Notes for simulating optimal damage output: GCD, weaving, and what we know vs what we need to parameterise.

---

## 1. Global cooldown (GCD)

- **Value:** **1.0 second (1000 ms)** is the standard figure used by addons (e.g. GCDMonitor Revised, Combat Metronome) and most community guides.
- **Alternative:** Some testing suggests the *effective* time between chained ability casts can be closer to **0.9 s** when ability queuing is used (you input the next ability slightly before the GCD ends). So:
  - **GCD = 1.0 s** is the safe, documented value to use as the *minimum time between ability activations*.
  - **~0.9 s** can be used as an optional “optimistic” cycle time if we model queuing (e.g. for high-end parse simulation).

**Recommendation for simulation:** Use **1.0 s** as the default GCD. Expose it as a constant (e.g. `GCD_SEC = 1.0`) so we can later test 0.9 s or make it build-specific if we find a patch note that changes it.

**Sources:**  
[Combat Metronome (GCD Tracker)](https://esoui.com/downloads/info2373-CombatMetronomeGCDTracker.html), [GCDMonitor Revised](https://www.esoui.com/downloads/info4050-GCDMonitorRevised.html), [forum discussion on cast times](https://forums.elderscrollsonline.com/en/discussion/300346/cast-times-for-all-abilities-and-attacks).

---

## 2. Weaving / animation cancelling

- **Weaving:** A light attack (LA) is used, then an ability is cast *immediately* so that the ability **cancels the rest of the LA animation**. The ability still goes on cooldown (GCD). So one “cycle” is: **LA + ability** within one GCD window.
- **Effect:** You get **two damage events per GCD** (one LA, one ability) instead of one ability only. That’s why “LA weaving” is mandatory for high DPS; guides often describe it as roughly **two actions per second** (one LA + one ability per second).
- **Timing:** The LA is very short (on the order of tens of ms); the ability fires and starts the 1 s GCD. There is no separate “LA cooldown” that blocks the next ability – the only hard limit is the GCD after the ability.
- **Heavy attacks:** Different mechanic (charge time, resource return, off-balance bonus). For a *DPS* rotation we usually model **light-attack weaving** only; heavy attacks can be added later for sustain or specific builds.

**Recommendation for simulation:**

- **Cycle length:** One cycle = **1.0 s** (tied to GCD).
- **Per cycle:** 1× light attack + 1× ability (when modelling a weaved rotation).
- **DoTs:** DoT skills still obey the GCD when you *cast* them, but their *ticks* occur on their own schedule (e.g. every 1 s or 2 s for X seconds). So in the same 1 s you might cast one spammable + have several DoTs ticking. The simulator needs to:
  - Advance time in steps (e.g. by GCD or by 0.1 s),
  - Apply ability damage on cast (and/or on first tick for channeled/DoT),
  - Apply LA damage once per cycle when “weaving” is on,
  - Apply DoT tick damage at the correct time offsets.

**Sources:**  
[Animation cancelling (Arzyelbuilds)](https://arzyelbuilds.com/animation-canceling-guide-eso/), [Alcast weaving guide](https://alcasthq.com/eso-weaving-beginner-guide-animation-canceling/), [UESP Combat / Light Attack](https://en.uesp.net/wiki/Online:Light_Attack).

---

## 3. Light attack damage

- **Scaling:** As of **Update 28**, light attack damage (all weapon types) scales from **highest of (Max Stamina + Weapon Damage) vs (Max Magicka + Spell Damage)** – i.e. the higher stat pool wins.
- **Cost:** No resource cost; LAs in combat grant the hidden buff that gives **3 Ultimate per second for 9 s** (refreshed on each LA).
- **Exact coefficient:** UESP and the forum guide don’t quote a single “skill coefficient” for LAs. To simulate LA damage we need either:
  - A **coefficient** (or equivalent formula) from datamining / addon / UESP (e.g. similar to `0.1 * MaxStat + 1.0 * MaxPower` with a known ratio), or
  - To **infer** it from parse data (e.g. “LA contributed X% of total damage” at known stats) and back out an effective coefficient.

**Recommendation:** Treat **light attack coefficient as a parameter** to be filled from UESP skill coefficient data (if LAs appear there), from another datamined source, or from a small calibration step using dummy parse data. Store it in the same format as other skills (e.g. in `skills` or a dedicated “global_combat” table) so one damage formula handles both LAs and abilities.

---

## 4. Damage formula (for abilities and LAs)

Community formula (PvE, single target), consistent with the forum guide and UESP:

- **Tooltip-style base:**  
  `(MaxStat + WeaponOrSpellDamage * 10.46) * SkillCoefficient * RankCoefficient`  
  (MaxStat = Max Magicka or Max Stamina depending on skill; 10.46 is the stat-to-power ratio, sometimes given as 10.5 in UESP coefficient data.)

- **Average damage including crit:**  
  `Base * (1 + CritChance * CritDamage) * (1 + DamageDone) * ArmorMitigation * (1 + DamageTaken)`  
  plus execute/bloodthirsty and other multiplicative terms as needed.

- **Skill coefficient:** Per-ability (from UESP [esoitem.uesp.net/viewSkillCoef.php](https://esoitem.uesp.net/viewSkillCoef.php)); we store in `skills.coefficient_json` and parse for the relevant placeholder (e.g. the main damage line).

**Recommendation:** Implement one **shared damage calculator** that takes (stat block, skill coefficient, buffs, target armour) and returns expected damage per hit (or per tick for DoTs). Use it for both abilities and LAs once we have an LA coefficient.

---

## 5. What we have vs what we need

| Item | Status | Action |
|------|--------|--------|
| GCD duration | **1.0 s** (0.9 s optional for queuing) | Use as constant; document in code. |
| Weave model | **1 LA + 1 ability per GCD** | Implement cycle-based or time-step simulator. |
| Ability coefficients | **UESP skill coefficient table** | Ingest into `skills.coefficient_json`; parse for base damage. |
| LA coefficient | **Not yet in our schema** | Find in UESP/datamine or infer from parses; add to DB or constants. [CombatMetrics](https://github.com/Solinur/CombatMetrics) (and similar addons) can provide combat logs / DPS parses for calibration. |
| Stat–power ratio (10.46 / 10.5) | **Documented** | Use in damage formula (match UESP ratio if different). |
| Cast vs channel | Abilities have cast times or channels | For a first pass, treat all as instant (GCD only); refine later with cast/channel times if needed. |

---

## 6. Static vs dynamic rotations (ESO)

**Static rotation:** A predetermined sequence of 6–12 skills repeated in the same order. The player memorizes the sequence and executes it on a fixed cycle; it works best when skill durations align (e.g. DoTs lasting 8s or 10s so they line up with a repeating pattern). Static rotations minimize downtime and overcasting because the order is chosen so that nothing expires too early or gets recast too late. They are generally easier to learn and execute consistently on a dummy.

**Dynamic rotation:** Abilities are cast based on **when their durations expire**, not a fixed order. The player watches DoT/buff timers and recasts whatever has expired (or is about to), using a spammable when nothing needs refreshing. This requires more active decision-making and works better when durations do not align neatly (e.g. long DoTs, or mixed 6s/8s/10s timers). In real fights, mechanics often force a more dynamic style.

**Implications for simulation:**

| Model    | How we approximate it | When to use |
|----------|------------------------|------------|
| **Static**  | Fixed cycle: assign each ability a fixed **hits (or casts) per second** from a repeating sequence. Our `rotation_dps` weighted sum is exactly this: `DPS = sum(damage_per_hit(a) * casts_per_sec(a))`. Weights = casts per second per ability in the static cycle. | Dummy parse, optimized fixed loop (e.g. “DoT A every 10s, DoT B every 8s, spammable fill”). |
| **Dynamic** | Priority-based: at each GCD, cast the **highest-priority** ability that has expired (or is about to), otherwise cast the spammable. Requires per-ability `duration_sec` (and optionally tick timing). Simulate time step-by-step and sum damage over a window. | When durations don’t align, or when comparing builds where uptime depends on expiry-driven recasts. |

**Recommendation:** Support both in code: (1) **Static** = current `rotation_dps(ability_weights)` with weights = casts/sec. (2) **Dynamic** = time-step sim with a priority-ordered list and `duration_sec` from `skills`; at each step choose “recast highest-priority expired DoT/buff, else spammable” and advance time by GCD. Use static for fast optimizer scoring; use dynamic for more accurate DPS when ability durations are known and matter.

**Source:** [ESO forum: Difference between static rotation and dynamic rotation](https://forums.elderscrollsonline.com/en/discussion/452574/difference-between-static-rotation-and-dynamic-rotation).

---

## 7. Cast times and durations in all calculations

All calculations that simulate or score rotations must account for:

| Concept | Schema / source | Where we use it |
|--------|------------------|------------------|
| **Cast time** | `skills.cast_time_sec` | Dynamic rotation: time advances by `max(GCD, cast_time_sec)` after each cast so channeled/long casts consume the correct time. Static rotation: weights (casts/sec) are supplied by the user and should be derived from a cycle that already respects cast times. |
| **Duration (DoT / HoT / buff / debuff)** | `skills.duration_sec`, `buffs.duration_sec` | **Recast timing:** In the dynamic rotation we recast when `duration_sec` has elapsed (expiry). **Damage per cast:** For DoTs, `damage_per_hit` uses one coefficient slot (UESP: often per-tick); total DoT damage = per-tick × (duration_sec / tick_interval_sec). We do not yet have `tick_interval_sec` in schema, so we treat the coefficient as the damage applied once per cast (or as total over duration if the data is stored that way). Buff/debuff effects (e.g. Major Vulnerability) are applied via parameters such as `target_damage_taken_pct`, not by reading `buffs` inside the damage formula. |

**Verification checklist:**

- **Static rotation (`rotation_dps`):** Weights = casts per second. When building these weights from a real rotation, the cycle length and cast counts must account for cast times (e.g. a 2 s channel = 0.5 casts/sec) and durations (DoT recast every duration_sec).
- **Dynamic rotation (`dynamic_rotation_dps`):** Uses `duration_sec` for when to recast; uses `cast_time_sec` for how much time each cast consumes (`t += max(GCD_SEC, cast_time_sec)` when available).
- **Damage (`damage_per_hit`):** Uses coefficients only; does not read duration or cast time. DoT total per cast would require tick interval (or number of ticks) to multiply per-tick damage; that is documented as a future extension where data exists.

---

## 8. Suggested next steps for simulation

1. **Constants module:**  Define `GCD_SEC = 1.0`, optional `GCD_QUEUED_SEC = 0.9`, and a placeholder `LIGHT_ATTACK_COEFFICIENT` (or load from DB once we have it).
2. **Damage formula:** Implement the formula in §4 (base from stat/power + coefficient, then crit, damage done, mitigation). Use it for abilities (from `skills`) and for LAs when coefficient is available.
3. **Static vs dynamic:** **Static** = `core.rotation.rotation_dps` (weighted sum = fixed cycle); **dynamic** = time-step sim with priority list and `duration_sec` (recast on expiry, else spammable). See §6.
4. **Simple rotation simulator:** For a given bar (list of ability ids + “weave” flag), advance time by GCD; each step apply 1 LA (if weave) + 1 ability; refresh DoTs as per their duration/tick. Sum damage over a fight length and divide by time for DPS.
5. **Calibration:** Once we have real parse logs (e.g. from [CombatMetrics](https://github.com/Solinur/CombatMetrics) or community numbers) for a known build, compare simulated DPS to actual and tune GCD/LA coefficient/DoT tick timing if needed.

This keeps our simulation aligned with how ESO actually limits rate of actions (GCD + weaving) and how damage is calculated, while leaving one clear unknown (LA coefficient) to be filled from data or calibration.

---

## 9. Optimal ultimate usage (bar assignment and tradeoff)

Builds typically run **two ultimates**: one for a passive, self-buff, debuff, or group/other-player buff; the other as the **main damage-dealing ultimate**. Bar assignment matters because the player spends the majority of time on the **front bar** (spamming), so the ultimate on that bar is the one that is "always there" for passive or situational use.

### Roles

| Role | Description | Examples |
|------|-------------|----------|
| **Passive / self-buff** | Slotted for a passive or self-buff (e.g. weapon/spell damage while slotted). Often not cast, or cast rarely. | Dawnbreaker (Fighters Guild): passive weapon and spell damage when slotted. |
| **Debuff** | Cast to apply an important debuff on the target (or area). Value = uptime and effect on group DPS. | Necromancer Flesh Atronach Colossus (Major Vulnerability or similar debuff). |
| **Group / other-player buff** | Cast to grant a buff to group or other players. Value = uptime and benefit to raid. | Sorcerer Storm Atronach: grants Major Berserk to group. |
| **Damage** | Primary use is to deal damage when cast. Value = damage per cast and casts per fight (ultimate gain). | Shooting Star, Dawnbreaker (as nuke), Flawless Dawnbreaker, etc. |

### Convention and tradeoff

- **Typical setup:** The **passive**, **debuff**, or **group-buff** ultimate is on the **front bar** (slots 1–6; slot 6 = ultimate). The **damage** ultimate is on the **back bar** (slots 7–12; slot 12 = ultimate). Rationale: you spam on the front bar, so the passive/buff/debuff ultimate is always available when needed without swapping; you swap to the back bar to drop DoTs or refresh and can fire the damage ultimate from there.
- **Tradeoff:** Sometimes the **debuff or group-buff** ultimate is on the **back bar** (e.g. for bar-space or rotation reasons). Then:
  - **Cost:** You must bar-swap to cast it, so uptime or cast frequency may drop (e.g. Colossus less often, or Storm Atronach delayed).
  - **Benefit:** The **damage** ultimate can be on the front bar, so it’s available without swapping when ultimate is full.
  - **Calculation:** Compare (a) front = buff/debuff, back = damage vs (b) front = damage, back = buff/debuff: model ultimate gain over time, cast frequency of each, and for (b) the lower effective uptime of the buff/debuff due to swap delay; choose the assignment that maximizes total contribution (damage + buff/debuff value).

### For simulation and scoring

- When a build has a **bar layout** (e.g. `recommended_build_scribed_skills` with `bar_slot_ord` 1–12, where 6 = front ultimate, 12 = back ultimate):
  - Tag each ultimate ability by **role** (passive_self_buff | debuff | group_buff | damage), e.g. from skill line, description, or a small lookup.
  - **Score bar assignment:** Prefer (passive/buff/debuff on front, damage on back); or compute expected DPS + buff/debuff value for both assignments and use the better one.
- **Ultimate gain:** LAs and combat give ultimate; model ultimate per second and ultimate cost per ability so that "casts per fight" of each ultimate can be estimated. Then damage ultimate contribution = casts × damage_per_cast; buff/debuff contribution = uptime × effect (e.g. Major Berserk 10% damage to group).
- Schema: Bar layout is in `recommended_build_scribed_skills` (bar_slot_ord 1–12). Ultimate *role* can be stored in a small lookup (e.g. `ability_id` → role) or derived from `buff_grants` and skill line when we add it; no new table is strictly required until we implement the tradeoff calculator.

---

## 10. Trial dummy (parse target) and fight duration

The standard way to measure a damage dealer’s output and approximate trial conditions is to parse on the **Target Iron Atronach, Trial** (housing training dummy). See [ESO-Hub: Target Iron Atronach, Trial](https://eso-hub.com/en/furniture/target-iron-atronach-trial).

### What the trial dummy provides

- **Equivalent to a veteran trial boss** for health, resistance, and behaviour (can be attacked; reassembles when destroyed).
- **Most buffs available in a trial:** The dummy applies performance buffs and self debuffs so that a parse on it approximates the buff environment a DD sees in a real trial. This gives a reasonable “end-goal” for parsing: simulate trial conditions on a single target.
- **Synergies:** It provides synergy opportunities so the player can proc **Undaunted** skill line passives (e.g. resource regeneration on synergy use). Sustain and rotation on the dummy are therefore representative of trial sustain when synergies are taken.

### What the trial dummy does not provide

The dummy does **not** apply every possible trial debuff or support effect. When simulating “full support” or comparing to in-trial parses, the following are typically **not** present on the dummy (and may be provided by specific sets or roles in a trial):

- **Crystal Weapon** (e.g. 1000 armour debuff).
- **Perfect Stagger** uptime from a dedicated Stone Giant DK.
- **Alkosh**, **Z'en**, **Martial Knowledge**, or other set-based debuffs/buffs that a dedicated support might run.

So: **parse DPS on the trial dummy** = “trial-like buffs + synergies, standard resistance, no extra debuff stacking.” For in-trial estimates with full support, one would add those debuffs (e.g. higher effective damage taken or lower effective resistance) in a separate scenario or calibration step.

### Fight duration from DPS

Given a target with **health pool** \(H\) and constant **DPS** \(D\):

\[
\text{duration\_sec} = \frac{H}{D}.
\]

For the **21M trial dummy** (\(H = 21\,000\,000\)):

- **DPS 80k** → duration ≈ 262 s (~4.4 min).
- **DPS 100k** → duration ≈ 210 s (3.5 min).
- **DPS 120k** → duration ≈ 175 s (~2.9 min).

So for a given build we can **approximate fight duration** over a **range of DPS** (e.g. 80k–120k) to get a duration range (e.g. ~175–262 s). This is used to reason about sustain (can the build hold the rotation for that long?), ultimate casts per fight, and time-dependent set effects. In code, use `core.rotation.TRIAL_DUMMY_HP` (21M) and `core.rotation.fight_duration_sec(dps, target_hp)` for these approximations. Our `simulation_targets` table has `trial_dummy_21m` (resistance 18200); the dummy’s HP is not stored in the table but is documented here and in the seed notes.

### Builds are dependent on per-trial, per-boss (and encounter type)

Optimisation is **not only** single-target boss damage. Build and set choices should be **dependent on**:

- **Per trial:** Comp and support sets (Alkosh, Z'en, Martial Knowledge, Crystal Weapon, etc.) change what buffs/debuffs are present, so effective target resistance and damage-taken vary. Which trial you are in drives scenario assumptions.
- **Per boss:** Within a trial, each boss has different resistance, HP, and mechanics (phases, invuln windows, movement). Some bosses have extra debuffs (e.g. Stagger) or favour different set choices (e.g. Harpooner's Kilt per-boss notes). Builds are chosen or optimised **per boss** for that context.
- **Encounter type – boss vs trash:** Between boss encounters, trials have **trash packs** – groups of enemies. Damage optimisation there is **AOE / multi-target**, not single-target. So we have at least two scenario types:
  - **Boss:** Single-target (or low target count) damage optimisation; parse-style or in-trial boss conditions.
  - **Trash:** AOE damage optimisation for packs; different sets, skills, and rotation priorities (cleave, DoT spread, etc.).

So **builds are dependent on per-trial, per-boss basis**, and on whether the encounter is a **boss** (single-target) or **trash** (AOE). We treat simulation conditions as a first-class concept: each scenario (trial + boss or trial + trash, plus optional buff/debuff assumptions) can have its own target stats, target count or AOE model, and set notes. The optimizer and advisor score or recommend builds **per scenario** (e.g. per trial, per boss, and for trash in that trial). Next steps: simulation targets or scenario profiles that distinguish single-target vs AOE; link trials/bosses and trash to those profiles; populate trial_boss_set_notes and, where needed, trash-pack or AOE scenario assumptions.
