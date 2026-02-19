"""
Stat block calculator: given race, sets, food, potion, mundus compute derived stats.

Aggregates flat and percent contributions from:
- race_effects (effect_type + magnitude from DB)
- mundus_stones (effect_type + magnitude from DB)
- set_bonuses (only where effect_type and magnitude are populated; UESP ingest leaves them NULL)
- foods / potions (effect_json or fallback constants when available)

Output: StatBlock dataclass used by the damage formula.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


# ESO stat-to-power ratio (MaxStat contribution to tooltip vs MaxPower). UESP often uses ~10.46.
STAT_POWER_RATIO = 10.46

# Base crit: 10% chance, 50% damage (before CP/buffs).
DEFAULT_CRIT_CHANCE = 0.10
DEFAULT_CRIT_DAMAGE = 0.50


@dataclass
class StatBlock:
    """Derived stats for one build configuration (race + gear + consumables + mundus)."""

    # Resources (flat)
    max_health: float = 0.0
    max_magicka: float = 0.0
    max_stamina: float = 0.0
    # Damage (flat)
    weapon_damage: float = 0.0
    spell_damage: float = 0.0
    # Resistances (flat)
    physical_resistance: float = 0.0
    spell_resistance: float = 0.0
    # Penetration (flat; often same for physical/spell in formulas)
    penetration: float = 0.0
    # Recovery (flat)
    health_recovery: float = 0.0
    magicka_recovery: float = 0.0
    stamina_recovery: float = 0.0
    # Percent modifiers (additive, e.g. 0.10 = 10% from Major Berserk)
    damage_done_pct: float = 0.0
    healing_done_pct: float = 0.0
    crit_chance: float = DEFAULT_CRIT_CHANCE
    crit_damage: float = DEFAULT_CRIT_DAMAGE
    # Critical rating (flat) if we have it; otherwise derived from crit_chance
    critical_rating: float = 0.0

    def max_stat_for_mechanic(self, mechanic: str | None) -> float:
        """Return MaxStat (Magicka or Stamina) for damage scaling. Heals may use Magicka."""
        if mechanic == "Stamina":
            return self.max_stamina
        return self.max_magicka

    def power_for_mechanic(self, mechanic: str | None) -> float:
        """Return Weapon or Spell Damage for the given resource mechanic."""
        if mechanic == "Stamina":
            return self.weapon_damage
        return self.spell_damage


# Map mundus/race effect_type (from DB) to StatBlock field names and whether we add or set.
# Format: effect_type -> (stat_attr, is_percent).
# Percent: magnitude 0.11 -> add 0.11 to crit_damage (11% bonus).
EFFECT_TYPE_TO_STAT: dict[str, tuple[str, bool]] = {
    # Mundus (from 10_seed_mundus_food_potions)
    "spell_damage": ("spell_damage", False),
    "magicka_recovery": ("magicka_recovery", False),
    "resistance": ("physical_resistance", False),  # applied to both; we add to both below
    "max_health": ("max_health", False),
    "penetration": ("penetration", False),
    "max_magicka": ("max_magicka", False),
    "healing_done": ("healing_done_pct", True),
    "stamina_recovery": ("stamina_recovery", False),
    "critical_damage": ("crit_damage", True),   # bonus e.g. 0.11
    "health_recovery_movement": ("health_recovery", False),
    "critical_rating": ("critical_rating", False),
    "max_stamina": ("max_stamina", False),
    "weapon_damage": ("weapon_damage", False),
    # Race effect_type = passive name (from 13_seed_race_effects)
    "Syrabane's Boon": ("max_magicka", False),
    "Elemental Talent": ("spell_damage", False),  # also weapon_damage; handled in code
    "Gift of Magnus": ("max_magicka", False),
    # "Spell Attunement" handled in _add_race_effects (spell_resistance only)
    # "Magicka Mastery" = cost reduction 7%; not a stat we aggregate here
    "Life Mender": ("healing_done_pct", True),
    "Argonian Resistance": ("max_health", False),
    "Resourceful": ("max_magicka", False),  # also max_stamina; handled in code
    "Hunter's Eye": ("penetration", False),
    "Y'ffre's Endurance": ("stamina_recovery", False),
    "Resist Affliction": ("max_stamina", False),
    "Ashlander": ("max_magicka", False),  # lava; skip damage taken
    "Dynamic": ("max_magicka", False),    # also max_stamina
    "Resist Flame": ("spell_resistance", False),
    "Ruination": ("spell_damage", False),  # also weapon_damage
    "Tough": ("max_health", False),
    "Imperial Mettle": ("max_stamina", False),
    "Red Diamond": ("damage_done_pct", True),  # cost reduction; approximate as small damage done
    "Robustness": ("health_recovery", False),  # all three recoveries; use health
    "Lunar Blessings": ("max_health", False),  # all three; use health as proxy
    "Feline Ambush": ("crit_damage", True),
    "Resist Frost": ("max_health", False),  # also frost res
    "Stalwart": ("max_stamina", False),
    # "Rugged" handled in _add_race_effects (physical_resistance + spell_resistance)
    "Brawny": ("max_stamina", False),
    "Unflinching Rage": ("max_health", False),
    "Swift Warrior": ("spell_damage", False),  # also weapon_damage
    "Conditioning": ("max_stamina", False),
    "Adrenaline Rush": ("stamina_recovery", False),  # on damage; treat as recovery
}

# Race effects that add to both weapon_damage and spell_damage (magnitude once).
RACE_DUAL_POWER: set[str] = {"Elemental Talent", "Ruination", "Swift Warrior"}

# Race effects that add to both max_magicka and max_stamina.
RACE_DUAL_RESOURCE: set[str] = {"Dynamic", "Resourceful"}


def _apply_magnitude(block: StatBlock, attr: str, magnitude: float, is_percent: bool) -> None:
    if magnitude is None:
        return
    if is_percent and attr in ("crit_damage", "healing_done_pct", "damage_done_pct"):
        setattr(block, attr, getattr(block, attr) + magnitude)
    else:
        setattr(block, attr, getattr(block, attr) + magnitude)


def _add_race_effects(conn: sqlite3.Connection, game_build_id: int, race_id: int, block: StatBlock) -> None:
    rows = conn.execute(
        "SELECT effect_type, magnitude FROM race_effects WHERE game_build_id = ? AND race_id = ?",
        (game_build_id, race_id),
    ).fetchall()
    for effect_type, magnitude in rows:
        if effect_type in RACE_DUAL_POWER and magnitude is not None:
            block.weapon_damage += magnitude
            block.spell_damage += magnitude
            continue
        if effect_type in RACE_DUAL_RESOURCE and magnitude is not None:
            half = magnitude / 2.0
            block.max_magicka += half
            block.max_stamina += half
            continue
        if effect_type == "Rugged" and magnitude is not None:
            block.physical_resistance += magnitude
            block.spell_resistance += magnitude
            continue
        if effect_type == "Spell Attunement" and magnitude is not None:
            block.spell_resistance += magnitude
            continue
        tup = EFFECT_TYPE_TO_STAT.get(effect_type)
        if tup:
            attr, is_percent = tup
            _apply_magnitude(block, attr, magnitude, is_percent)


def _add_mundus(conn: sqlite3.Connection, game_build_id: int, mundus_id: int | None, block: StatBlock) -> None:
    if mundus_id is None:
        return
    row = conn.execute(
        "SELECT effect_type, magnitude FROM mundus_stones WHERE game_build_id = ? AND mundus_id = ?",
        (game_build_id, mundus_id),
    ).fetchone()
    if not row:
        return
    effect_type, magnitude = row
    if effect_type == "resistance" and magnitude is not None:
        block.physical_resistance += magnitude
        block.spell_resistance += magnitude
        return
    tup = EFFECT_TYPE_TO_STAT.get(effect_type)
    if tup:
        attr, is_percent = tup
        _apply_magnitude(block, attr, magnitude, is_percent)


def _add_set_bonuses(
    conn: sqlite3.Connection,
    game_build_id: int,
    set_pieces: list[tuple[int, int]],
    block: StatBlock,
) -> None:
    """Add bonuses from set_bonuses where (game_id, num_pieces) is in set_pieces and effect_type/magnitude are set."""
    for game_id, num_pieces in set_pieces:
        rows = conn.execute(
            """SELECT effect_type, magnitude FROM set_bonuses
               WHERE game_build_id = ? AND game_id = ? AND num_pieces = ? AND effect_type IS NOT NULL AND magnitude IS NOT NULL""",
            (game_build_id, game_id, num_pieces),
        ).fetchall()
        for effect_type, magnitude in rows:
            tup = EFFECT_TYPE_TO_STAT.get(effect_type)
            if tup:
                attr, is_percent = tup
                _apply_magnitude(block, attr, magnitude, is_percent)


def _add_food_potion(
    conn: sqlite3.Connection,
    game_build_id: int,
    food_id: int | None,
    potion_id: int | None,
    block: StatBlock,
) -> None:
    """Add food/potion contributions. Seed data has no effect_type/magnitude; use effect_json if present or skip."""
    # Optional: parse effect_json when populated (e.g. {"max_health": 1000, "max_magicka": 1000, ...})
    if food_id is not None:
        row = conn.execute(
            "SELECT effect_json FROM foods WHERE game_build_id = ? AND food_id = ?",
            (game_build_id, food_id),
        ).fetchone()
        if row and row[0]:
            import json
            try:
                data = json.loads(row[0])
                for key in ("max_health", "max_magicka", "max_stamina", "health_recovery", "magicka_recovery", "stamina_recovery"):
                    if key in data and isinstance(data[key], (int, float)):
                        setattr(block, key, getattr(block, key) + float(data[key]))
            except (json.JSONDecodeError, TypeError):
                pass
    if potion_id is not None:
        row = conn.execute(
            "SELECT effect_json FROM potions WHERE game_build_id = ? AND potion_id = ?",
            (game_build_id, potion_id),
        ).fetchone()
        if row and row[0]:
            import json
            try:
                data = json.loads(row[0])
                for key in ("weapon_damage", "spell_damage", "crit_chance", "crit_damage"):
                    if key in data and isinstance(data[key], (int, float)):
                        setattr(block, key, getattr(block, key) + float(data[key]))
            except (json.JSONDecodeError, TypeError):
                pass


def _apply_reference_caps(
    conn: sqlite3.Connection,
    game_build_id: int,
    block: StatBlock,
) -> None:
    """Optionally clamp stats to reference caps from stat_modifier_reference (Standalone Calculator)."""
    try:
        from .stat_reference import get_reference_value_by_name
    except ImportError:
        return
    # Crit damage bonus cap (e.g. 125% total -> 0.25 bonus from base 100%)
    cap = get_reference_value_by_name(conn, game_build_id, "buff_pct", "Critical Damage", prefer_effective=True)
    if cap is not None and block.crit_damage > cap:
        block.crit_damage = cap
    cap = get_reference_value_by_name(conn, game_build_id, "base_stat", "Critical Damage", prefer_effective=True)
    if cap is not None and block.crit_damage > cap:
        block.crit_damage = cap


def compute_stat_block(
    conn: sqlite3.Connection,
    game_build_id: int,
    race_id: int,
    set_pieces: list[tuple[int, int]] | None = None,
    food_id: int | None = None,
    potion_id: int | None = None,
    mundus_id: int | None = None,
    front_bar_weapons: tuple[str | None, str | None] | None = None,
) -> StatBlock:
    """
    Compute derived stat block from race, set bonuses, food, potion, mundus, and optional weapon types.

    set_pieces: list of (game_id, num_pieces) for each set that is at that piece count (e.g. [(123, 5), (456, 2)]).
    front_bar_weapons: (main_hand_type, off_hand_type) for weapon-type bonuses (e.g. Twin Blade and Blunt).
      When dual wielding different 1H types, effects from both apply at half strength.
    If stat_modifier_reference is populated (from ingest_xlsx References for Stats), reference caps may be applied.
    """
    block = StatBlock()
    _add_race_effects(conn, game_build_id, race_id, block)
    _add_mundus(conn, game_build_id, mundus_id, block)
    if set_pieces:
        _add_set_bonuses(conn, game_build_id, set_pieces, block)
    _add_food_potion(conn, game_build_id, food_id, potion_id, block)
    if front_bar_weapons is not None:
        from .weapon_type import apply_weapon_bonuses_to_stat_block, get_weapon_bonuses_for_bar
        bonuses = get_weapon_bonuses_for_bar(conn, game_build_id, front_bar_weapons[0], front_bar_weapons[1])
        apply_weapon_bonuses_to_stat_block(block, bonuses)
    _apply_reference_caps(conn, game_build_id, block)
    return block
