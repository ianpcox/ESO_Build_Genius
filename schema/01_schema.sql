-- ESO Build Genius - Component-first schema
-- Each section is one component with a single responsibility. Builds are composition only (references to component IDs).
-- Versioned data uses game_build_id where the game changes per patch.

-- =============================================================================
-- VERSIONING (patch/snapshot id only)
-- Single responsibility: identify which game patch this data belongs to.
-- =============================================================================
CREATE TABLE IF NOT EXISTS game_builds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT NOT NULL,           -- e.g. 'Update 48 Incremental 3'
    api_version     TEXT,                   -- e.g. '101047' from UESP
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =============================================================================
-- LOOKUPS (fixed reference lists; no game_build_id)
-- Single responsibility: canonical ids and names for slots, set types, class, role.
-- =============================================================================
CREATE TABLE IF NOT EXISTS equipment_slots (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS set_types (
    id              TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS classes (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS roles (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

-- =============================================================================
-- COMPONENT: RACE
-- Single responsibility: what races exist and what passives they have (per build).
-- =============================================================================
CREATE TABLE IF NOT EXISTS races (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS race_effects (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    race_id         INTEGER NOT NULL REFERENCES races(id),
    effect_ord      INTEGER NOT NULL,
    effect_text     TEXT,
    effect_type     TEXT,
    magnitude       REAL,
    PRIMARY KEY (game_build_id, race_id, effect_ord)
);

-- =============================================================================
-- COMPONENT: EQUIPMENT SET (UESP-aligned: setSummary, setBonusDesc, itemSlots)
-- Single responsibility: what item sets exist, their bonuses, and which slots they can occupy.
-- =============================================================================
CREATE TABLE IF NOT EXISTS set_summary (
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    game_id             INTEGER NOT NULL,
    set_name            TEXT NOT NULL,
    type                TEXT NOT NULL REFERENCES set_types(id),
    set_max_equip_count INTEGER NOT NULL,
    PRIMARY KEY (game_build_id, game_id)
);

CREATE TABLE IF NOT EXISTS set_bonuses (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    game_id         INTEGER NOT NULL,
    num_pieces      INTEGER NOT NULL,
    set_bonus_desc  TEXT NOT NULL,
    effect_type     TEXT,
    magnitude       REAL,
    PRIMARY KEY (game_build_id, game_id, num_pieces),
    FOREIGN KEY (game_build_id, game_id) REFERENCES set_summary(game_build_id, game_id)
);

CREATE TABLE IF NOT EXISTS set_item_slots (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    game_id         INTEGER NOT NULL,
    slot_id         INTEGER NOT NULL REFERENCES equipment_slots(id),
    PRIMARY KEY (game_build_id, game_id, slot_id),
    FOREIGN KEY (game_build_id, game_id) REFERENCES set_summary(game_build_id, game_id)
);

-- =============================================================================
-- COMPONENT: SKILL
-- Single responsibility: what skills/abilities exist and their coefficients/tooltips.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skills (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    ability_id      INTEGER NOT NULL,
    name            TEXT NOT NULL,
    skill_line      TEXT,
    skill_line_id   INTEGER,
    class_name      TEXT,
    mechanic        TEXT,
    description     TEXT,
    coefficient_json TEXT,  -- UESP skillCoef / viewSkillCoef: JSON array of { type, a, b, c, R, avg } per slot (1..6)
    base_tooltip    REAL,
    adps            REAL,
    skill_damage_type TEXT,
    range_text      TEXT,
    cost            INTEGER,
    duration_sec    REAL,
    cast_time_sec   REAL,
    crux_required   INTEGER,
    data_source    TEXT,
    update_label   TEXT,
    PRIMARY KEY (game_build_id, ability_id)
);

-- =============================================================================
-- COMPONENT: BUFF
-- Single responsibility: what buffs/debuffs exist (name, effect type, magnitude).
-- =============================================================================
CREATE TABLE IF NOT EXISTS buffs (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    buff_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_type     TEXT,
    magnitude       REAL,
    duration_sec    REAL,
    effect_text     TEXT,
    PRIMARY KEY (game_build_id, buff_id)
);

-- =============================================================================
-- COMPONENT: MUNDUS
-- Single responsibility: what mundus stones exist and their effects.
-- =============================================================================
CREATE TABLE IF NOT EXISTS mundus_stones (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    mundus_id       INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_text     TEXT NOT NULL,
    effect_type     TEXT,
    magnitude       REAL,
    PRIMARY KEY (game_build_id, mundus_id)
);

-- =============================================================================
-- COMPONENT: FOOD
-- Single responsibility: what food/drink exists and their stat effects.
-- =============================================================================
CREATE TABLE IF NOT EXISTS foods (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    food_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,
    duration_sec    INTEGER,
    effect_text     TEXT,
    effect_json     TEXT,
    PRIMARY KEY (game_build_id, food_id)
);

-- =============================================================================
-- COMPONENT: POTION
-- Single responsibility: what potions exist and their effects/cooldowns.
-- =============================================================================
CREATE TABLE IF NOT EXISTS potions (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    potion_id       INTEGER NOT NULL,
    name            TEXT NOT NULL,
    duration_sec    REAL,
    cooldown_sec    REAL,
    effect_text     TEXT,
    effect_json     TEXT,
    PRIMARY KEY (game_build_id, potion_id)
);

-- =============================================================================
-- COMPONENT: TRAIT (weapon, armor, jewelry)
-- Single responsibility: canonical trait names for build equipment.
-- =============================================================================
CREATE TABLE IF NOT EXISTS traits (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    slot_type   TEXT NOT NULL,  -- 'weapon', 'armor', 'jewelry'
    UNIQUE (name, slot_type)
);

-- =============================================================================
-- INGEST PROVENANCE (optional)
-- Single responsibility: record which run populated which build's data.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ingest_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    source_type     TEXT NOT NULL,
    source_path     TEXT,
    ingested_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =============================================================================
-- COMPONENT: TRIAL (optional; for per-boss context later)
-- Single responsibility: trials, bosses, and trial/boss metadata.
-- =============================================================================
CREATE TABLE IF NOT EXISTS trials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS trial_bosses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id        INTEGER NOT NULL REFERENCES trials(id),
    name            TEXT NOT NULL,
    UNIQUE (trial_id, name)
);

-- =============================================================================
-- BUILD (composition only – references to components; no component data here)
-- Single responsibility: store which race, class, sets, mundus, food, potion
-- are combined for a given recommended build. All real data lives in component tables.
-- =============================================================================
CREATE TABLE IF NOT EXISTS recommended_builds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    class_id            INTEGER NOT NULL REFERENCES classes(id),
    role_id             INTEGER NOT NULL REFERENCES roles(id),
    race_id             INTEGER NOT NULL REFERENCES races(id),
    mundus_id           INTEGER NOT NULL,
    food_id             INTEGER NOT NULL,
    potion_id           INTEGER NOT NULL,
    score_dps           REAL,
    score_notes         TEXT,
    weapon_type         TEXT,
    simulation_target_id INTEGER,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_build_id, mundus_id) REFERENCES mundus_stones(game_build_id, mundus_id),
    FOREIGN KEY (game_build_id, food_id)   REFERENCES foods(game_build_id, food_id),
    FOREIGN KEY (game_build_id, potion_id)  REFERENCES potions(game_build_id, potion_id)
);

CREATE TABLE IF NOT EXISTS recommended_build_equipment (
    recommended_build_id INTEGER NOT NULL REFERENCES recommended_builds(id) ON DELETE CASCADE,
    slot_id             INTEGER NOT NULL REFERENCES equipment_slots(id),
    game_id             INTEGER NOT NULL,
    game_build_id       INTEGER NOT NULL,
    trait_id            INTEGER REFERENCES traits(id),
    glyph_id            INTEGER,
    weapon_poison_id    INTEGER,
    PRIMARY KEY (recommended_build_id, slot_id),
    FOREIGN KEY (game_build_id, game_id) REFERENCES set_summary(game_build_id, game_id)
);

-- =============================================================================
-- SEED DATA (lookups and stable reference lists)
-- =============================================================================
INSERT OR IGNORE INTO set_types (id) VALUES
    ('crafted'), ('dungeon'), ('trial'), ('overland'), ('arena'), ('monster'), ('mythic'), ('pvp');

INSERT OR IGNORE INTO equipment_slots (id, name) VALUES
    (1, 'head'), (2, 'shoulders'), (3, 'chest'), (4, 'legs'), (5, 'feet'),
    (6, 'hands'), (7, 'waist'), (8, 'front_main'), (9, 'front_off'), (10, 'back_main'), (11, 'back_off');

INSERT OR IGNORE INTO classes (id, name) VALUES
    (1, 'Dragonknight'), (2, 'Sorcerer'), (3, 'Nightblade'), (4, 'Templar'),
    (5, 'Warden'), (6, 'Necromancer'), (7, 'Arcanist');

INSERT OR IGNORE INTO roles (id, name) VALUES
    (1, 'dd'), (2, 'healer'), (3, 'tank'), (4, 'support_dd');

INSERT OR IGNORE INTO races (id, name) VALUES
    (1, 'Altmer'), (2, 'Argonian'), (3, 'Bosmer'), (4, 'Breton'), (5, 'Dunmer'),
    (6, 'Imperial'), (7, 'Khajiit'), (8, 'Nord'), (9, 'Orc'), (10, 'Redguard');
