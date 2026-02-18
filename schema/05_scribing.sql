-- Scribing: base skill + up to 3 additional effects (e.g. Focus, Signature, Affix scripts).
-- Greatly increases build diversity and complicates "optimal" (many combinations per slot).

-- =============================================================================
-- SCRIBE EFFECT SLOTS (lookup)
-- ESO uses e.g. Focus / Signature / Affix as the three script slots.
-- =============================================================================
CREATE TABLE IF NOT EXISTS scribe_effect_slots (
    id              INTEGER PRIMARY KEY,   -- 1, 2, 3
    name            TEXT NOT NULL UNIQUE   -- e.g. 'Focus', 'Signature', 'Affix'
);

-- =============================================================================
-- SCRIBE EFFECTS (catalog per game build)
-- Pool of effects that can be added to a base skill; each effect belongs to one slot.
-- =============================================================================
CREATE TABLE IF NOT EXISTS scribe_effects (
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    scribe_effect_id    INTEGER NOT NULL,
    name                TEXT NOT NULL,
    slot_id             INTEGER NOT NULL REFERENCES scribe_effect_slots(id),
    effect_text         TEXT,
    effect_type         TEXT,
    magnitude           REAL,
    resource_type       TEXT,               -- magicka / stamina if slot determines it
    PRIMARY KEY (game_build_id, scribe_effect_id),
    FOREIGN KEY (game_build_id) REFERENCES game_builds(id)
);

-- =============================================================================
-- SKILL SCRIBE COMPATIBILITY (optional)
-- Which scribe effects can be applied to which base skills (if restricted by game).
-- If every effect can apply to every skill, this table can stay empty or be filled
-- for validation only.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_scribe_compatibility (
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    ability_id          INTEGER NOT NULL,
    scribe_effect_id    INTEGER NOT NULL,
    PRIMARY KEY (game_build_id, ability_id, scribe_effect_id),
    FOREIGN KEY (game_build_id, ability_id) REFERENCES skills(game_build_id, ability_id),
    FOREIGN KEY (game_build_id, scribe_effect_id) REFERENCES scribe_effects(game_build_id, scribe_effect_id)
);

-- =============================================================================
-- RECOMMENDED BUILD SCRIBED SKILLS (bar layout with scribing)
-- For each bar slot: base ability + 0..3 scribe effects (order = slot 1, 2, 3).
-- NULL effect id = no script in that slot (base skill only or fewer than 3).
-- Scribing multiplies the space of "optimal" builds; optimization may need to
-- constrain or sample over scribed variants.
-- =============================================================================
CREATE TABLE IF NOT EXISTS recommended_build_scribed_skills (
    recommended_build_id INTEGER NOT NULL REFERENCES recommended_builds(id) ON DELETE CASCADE,
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    bar_slot_ord        INTEGER NOT NULL,   -- position on bar (e.g. 1..10)
    ability_id          INTEGER NOT NULL,
    scribe_effect_id_1   INTEGER NULL,
    scribe_effect_id_2   INTEGER NULL,
    scribe_effect_id_3   INTEGER NULL,
    PRIMARY KEY (recommended_build_id, bar_slot_ord),
    FOREIGN KEY (game_build_id, ability_id) REFERENCES skills(game_build_id, ability_id),
    FOREIGN KEY (game_build_id, scribe_effect_id_1) REFERENCES scribe_effects(game_build_id, scribe_effect_id),
    FOREIGN KEY (game_build_id, scribe_effect_id_2) REFERENCES scribe_effects(game_build_id, scribe_effect_id),
    FOREIGN KEY (game_build_id, scribe_effect_id_3) REFERENCES scribe_effects(game_build_id, scribe_effect_id),
    CHECK (bar_slot_ord >= 1 AND bar_slot_ord <= 12)
);

-- =============================================================================
-- SEED: scribe effect slots (Focus, Signature, Affix)
-- =============================================================================
INSERT OR IGNORE INTO scribe_effect_slots (id, name) VALUES
    (1, 'Focus'),
    (2, 'Signature'),
    (3, 'Affix');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scribe_effects_build_slot ON scribe_effects(game_build_id, slot_id);
CREATE INDEX IF NOT EXISTS idx_skill_scribe_compat_ability ON skill_scribe_compatibility(game_build_id, ability_id);
CREATE INDEX IF NOT EXISTS idx_recommended_build_scribed_skills_build ON recommended_build_scribed_skills(recommended_build_id);
