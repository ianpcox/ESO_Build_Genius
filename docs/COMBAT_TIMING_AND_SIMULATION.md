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
| LA coefficient | **Not yet in our schema** | Find in UESP/datamine or infer from parses; add to DB or constants. |
| Stat–power ratio (10.46 / 10.5) | **Documented** | Use in damage formula (match UESP ratio if different). |
| Cast vs channel | Abilities have cast times or channels | For a first pass, treat all as instant (GCD only); refine later with cast/channel times if needed. |

---

## 6. Suggested next steps for simulation

1. **Constants module:** Define `GCD_SEC = 1.0`, optional `GCD_QUEUED_SEC = 0.9`, and a placeholder `LIGHT_ATTACK_COEFFICIENT` (or load from DB once we have it).
2. **Damage formula:** Implement the formula in §4 (base from stat/power + coefficient, then crit, damage done, mitigation). Use it for abilities (from `skills`) and for LAs when coefficient is available.
3. **Simple rotation simulator:** For a given bar (list of ability ids + “weave” flag), advance time by GCD; each step apply 1 LA (if weave) + 1 ability; refresh DoTs as per their duration/tick. Sum damage over a fight length (e.g. 21M dummy) and divide by time for DPS.
4. **Calibration:** Once we have real parse logs (or community numbers) for a known build, compare simulated DPS to actual and tune GCD/LA coefficient/DoT tick timing if needed.

This keeps our simulation aligned with how ESO actually limits rate of actions (GCD + weaving) and how damage is calculated, while leaving one clear unknown (LA coefficient) to be filled from data or calibration.
