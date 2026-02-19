-- Glyphs (item enchantments) and weapon poisons. Traits table is in 01_schema.sql.
-- Build equipment can reference trait_id (01), glyph_id, weapon_poison_id per slot (nullable).

-- =============================================================================
-- COMPONENT: GLYPH (item enchantment for weapon, armor, or jewelry)
-- Source: UESP Online:Glyphs
-- =============================================================================
CREATE TABLE IF NOT EXISTS glyphs (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    glyph_id        INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_text     TEXT,
    slot_kind       TEXT NOT NULL,  -- 'weapon', 'armor', 'jewelry'
    effect_json     TEXT,          -- structured effect for tradeoff (e.g. damage, cooldown_sec)
    PRIMARY KEY (game_build_id, glyph_id)
);

-- =============================================================================
-- COMPONENT: WEAPON POISON (applied to weapon; separate from consumable potions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS weapon_poisons (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    poison_id       INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_text     TEXT,
    duration_sec    REAL,
    effect_json     TEXT,          -- structured effect for tradeoff (e.g. dot damage, debuff)
    PRIMARY KEY (game_build_id, poison_id)
);

-- Build equipment columns (trait_id, glyph_id, weapon_poison_id) are defined in 01_schema.sql.
-- Logical FKs: (game_build_id, glyph_id) -> glyphs, (game_build_id, weapon_poison_id) -> weapon_poisons.
