"""
Tradeoff between weapon enchants (glyphs) and weapon poisons.

Weapon slots can have either a glyph or a poison; this module estimates the impact of each
so users can compare. Uses effect_json from glyphs and weapon_poisons when available.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .damage import ARMOR_CONSTANT, armor_mitigation_multiplier
from .stat_block import StatBlock


@dataclass
class EnchantImpact:
    """Estimated impact of a weapon glyph (enchant)."""
    dps_contribution: float  # effective DPS from damage/buff/debuff
    heal_per_sec: float = 0.0
    shield_per_sec: float = 0.0
    description: str = ""


@dataclass
class PoisonImpact:
    """Estimated impact of a weapon poison."""
    dps_contribution: float
    damage_taken_pct: float = 0.0  # e.g. 0.10 for 10% vuln
    description: str = ""


@dataclass
class TradeoffResult:
    """Comparison of glyph vs poison for one weapon slot."""
    glyph_impact: EnchantImpact
    poison_impact: PoisonImpact
    recommendation: str  # "glyph", "poison", or "situational"
    note: str = ""


def _parse_effect_json(effect_json: str | None) -> dict[str, Any] | None:
    if not effect_json or not effect_json.strip():
        return None
    try:
        out = json.loads(effect_json)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def glyph_impact(
    effect_json: str | None,
    stat_block: StatBlock,
    target_resistance: float,
    hits_per_sec: float = 1.0,
) -> EnchantImpact:
    """
    Estimate the impact of a weapon glyph.

    effect_json: from glyphs.effect_json (e.g. type=damage, damage=645, cooldown_sec=4).
    hits_per_sec: approximate weapon hits per second (procs per second capped by cooldown).
    """
    ej = _parse_effect_json(effect_json)
    if not ej:
        return EnchantImpact(0.0, description="Unknown or no effect data")

    t = ej.get("type") or ""
    mitigation = armor_mitigation_multiplier(
        target_resistance,
        stat_block.penetration,
        ARMOR_CONSTANT,
    )
    crit_mult = 1.0 + stat_block.crit_chance * stat_block.crit_damage

    if t == "damage":
        dmg = float(ej.get("damage") or 0)
        cd = float(ej.get("cooldown_sec") or 4.0)
        procs_per_sec = min(1.0 / cd, hits_per_sec) if cd > 0 else hits_per_sec
        dps = dmg * mitigation * crit_mult * procs_per_sec
        return EnchantImpact(dps_contribution=dps, description=f"Proc damage ~{dmg} every {cd}s")

    if t == "buff" and ej.get("stat") == "weapon_spell_damage":
        amount = float(ej.get("amount") or 0)
        duration = float(ej.get("duration_sec") or 5.0)
        cd = float(ej.get("cooldown_sec") or 5.0)
        uptime = duration / cd if cd > 0 else 1.0
        # Approximate: +258 W/S damage adds ~2-3% of base; use a simple scale (e.g. 0.02 * base_dps equiv)
        # We don't have base_dps here, so report as effective flat damage equiv (amount * uptime * scale factor)
        equiv_dps = amount * uptime * 0.015  # rough: 258 * 1.0 * 0.015 ~ 3.9 "virtual" DPS per point
        return EnchantImpact(dps_contribution=equiv_dps, description=f"Buff +{amount} W/S, ~{uptime*100:.0f}% uptime")

    if t == "absorb":
        dmg = float(ej.get("damage") or 0)
        cd = float(ej.get("cooldown_sec") or 4.0)
        procs_per_sec = min(1.0 / cd, hits_per_sec) if cd > 0 else hits_per_sec
        dps = dmg * mitigation * crit_mult * procs_per_sec
        heal = float(ej.get("heal") or ej.get("amount") or 0) * procs_per_sec
        return EnchantImpact(dps_contribution=dps, heal_per_sec=heal, description="Damage + absorb")

    if t == "debuff" and (ej.get("stat") == "resistance" or ej.get("stat") == "armor"):
        amount = float(ej.get("amount") or 0)
        duration = float(ej.get("duration_sec") or 5.0)
        cd = float(ej.get("cooldown_sec") or 5.0)
        uptime = duration / cd if cd > 0 else 1.0
        # Reducing target resistance increases all damage; equiv to ~(1/new_mit - 1/old_mit)*base_dps. Simplified: treat as small DPS gain.
        equiv_dps = amount * uptime * 0.008  # rough scaling
        return EnchantImpact(dps_contribution=equiv_dps, description=f"Breach -{amount} resist, ~{uptime*100:.0f}% uptime")

    if t == "prismatic":
        dmg = float(ej.get("damage") or 0)
        cd = float(ej.get("cooldown_sec") or 4.0)
        procs_per_sec = min(1.0 / cd, hits_per_sec) if cd > 0 else hits_per_sec
        dps = dmg * mitigation * crit_mult * procs_per_sec
        heal = float(ej.get("heal") or 0) * procs_per_sec
        return EnchantImpact(dps_contribution=dps, heal_per_sec=heal, description="Prismatic damage + heal + resources")

    if t == "shield":
        amount = float(ej.get("amount") or 0)
        cd = float(ej.get("cooldown_sec") or 5.0)
        shield_per_sec = amount / cd if cd > 0 else 0
        return EnchantImpact(dps_contribution=0.0, shield_per_sec=shield_per_sec, description="Damage shield")

    return EnchantImpact(0.0, description=f"Unmodeled type: {t}")


def poison_impact(
    effect_json: str | None,
    duration_sec: float | None,
    stat_block: StatBlock,
    target_resistance: float,
    applications_per_sec: float = 0.5,
) -> PoisonImpact:
    """
    Estimate the impact of a weapon poison.

    effect_json: from weapon_poisons.effect_json.
    duration_sec: from weapon_poisons.duration_sec (fallback if not in effect_json).
    applications_per_sec: how often the poison is applied (e.g. 0.5 = every 2s from LAs).
    """
    ej = _parse_effect_json(effect_json)
    dur = duration_sec
    if ej:
        dur = dur or float(ej.get("duration_sec") or 4.0)
    else:
        dur = dur or 4.0

    if not ej:
        return PoisonImpact(0.0, description="Unknown or no effect data")

    t = ej.get("type") or ""
    mitigation = armor_mitigation_multiplier(
        target_resistance,
        stat_block.penetration,
        ARMOR_CONSTANT,
    )
    crit_mult = 1.0 + stat_block.crit_chance * stat_block.crit_damage

    if t == "dot":
        dmg = float(ej.get("damage") or 0)
        if dur <= 0:
            return PoisonImpact(0.0, description="DoT with no duration")
        # Total damage per application; applications_per_sec caps how often we reapply
        damage_per_app = dmg * mitigation * crit_mult
        dps = damage_per_app / dur * min(1.0, applications_per_sec * dur)
        return PoisonImpact(dps_contribution=dps, description=f"DoT {dmg} over {dur}s")

    if t == "debuff" and "damage_taken_pct" in ej:
        pct = float(ej.get("damage_taken_pct") or 0)
        # This multiplies all your damage; we report it as damage_taken_pct and let caller combine with base_dps
        return PoisonImpact(
            dps_contribution=0.0,
            damage_taken_pct=pct,
            description=f"Target takes {pct*100:.0f}% more damage for {dur}s",
        )

    return PoisonImpact(0.0, description=f"Unmodeled type: {t}")


def compare_glyph_vs_poison(
    glyph_effect_json: str | None,
    poison_effect_json: str | None,
    poison_duration_sec: float | None,
    stat_block: StatBlock,
    target_resistance: float = 18200.0,
    hits_per_sec: float = 1.0,
    poison_applications_per_sec: float = 0.5,
    base_dps: float = 0.0,
) -> TradeoffResult:
    """
    Compare impact of a weapon glyph vs a weapon poison.

    base_dps: your rotation DPS without glyph/poison; used to value vulnerability poison (base_dps * damage_taken_pct).
    Returns TradeoffResult with glyph_impact, poison_impact, recommendation, and note.
    """
    g = glyph_impact(glyph_effect_json, stat_block, target_resistance, hits_per_sec)
    p = poison_impact(
        poison_effect_json,
        poison_duration_sec,
        stat_block,
        target_resistance,
        poison_applications_per_sec,
    )

    poison_total_dps = p.dps_contribution
    if p.damage_taken_pct > 0 and base_dps > 0:
        poison_total_dps += base_dps * p.damage_taken_pct

    glyph_total = g.dps_contribution + g.heal_per_sec * 0.1  # optional: value heal as equiv DPS
    poison_total = poison_total_dps

    if glyph_total > poison_total * 1.05:
        rec = "glyph"
        note = f"Glyph contributes ~{glyph_total:.0f} equiv DPS vs poison ~{poison_total:.0f}."
    elif poison_total > glyph_total * 1.05:
        rec = "poison"
        note = f"Poison contributes ~{poison_total:.0f} equiv DPS vs glyph ~{glyph_total:.0f}."
    else:
        rec = "situational"
        note = f"Close: glyph ~{glyph_total:.0f}, poison ~{poison_total:.0f}. Consider survivability (absorb/shield) vs group vuln."

    return TradeoffResult(
        glyph_impact=g,
        poison_impact=p,
        recommendation=rec,
        note=note,
    )
