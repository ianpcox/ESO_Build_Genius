-- ESO Build Genius - SQLite schema
-- All game data is versioned by game_build_id. Run for a single build at a time or store multiple builds.

-- Build / versioning
CREATE TABLE IF NOT EXISTS game_builds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT NOT NULL,           -- e.g. 'Update 48 Incremental 3'
    api_version     TEXT,                   -- e.g. '101047' from UESP
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Reference: equipment slot names (fixed list)
CREATE TABLE IF NOT EXISTS equipment_slots (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE    -- head, shoulders, chest, legs, feet, hands, waist, front_main, front_off, back_main, back_off
);

-- Reference: ESO classes (fixed list)
CREATE TABLE IF NOT EXISTS classes (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE    -- Dragonknight, Sorcerer, Nightblade, Templar, Warden, Necromancer, Arcanist
);

-- Reference: roles
CREATE TABLE IF NOT EXISTS roles (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE    -- dd, healer, tank, support_dd
);

-- Ingest provenance (optional)
CREATE TABLE IF NOT EXISTS ingest_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    source_type     TEXT NOT NULL,          -- 'addon_export', 'uesp_skill_coef', 'uesp_set_summary'
    source_path     TEXT,
    ingested_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- Races (names stable; effects can change per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS races (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS race_effects (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    race_id         INTEGER NOT NULL REFERENCES races(id),
    effect_ord      INTEGER NOT NULL,      -- 1, 2, ... for ordering
    effect_text     TEXT,                 -- e.g. 'Increases Max Stamina by 2000'
    effect_type     TEXT,                 -- optional: 'max_stamina', 'recovery', etc.
    magnitude       REAL,                 -- optional numeric for optimizer
    PRIMARY KEY (game_build_id, race_id, effect_ord)
);

-- ---------------------------------------------------------------------------
-- Item sets (versioned per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS set_types (
    id              TEXT PRIMARY KEY       -- 'crafted', 'dungeon', 'trial', 'overland', 'arena', 'monster', 'mythic', 'pvp'
);

CREATE TABLE IF NOT EXISTS item_sets (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    set_id          INTEGER NOT NULL,      -- game's numeric set id
    name            TEXT NOT NULL,
    set_type        TEXT NOT NULL REFERENCES set_types(id),
    max_pieces      INTEGER NOT NULL,      -- 5 normal, 2 monster, 1 mythic
    PRIMARY KEY (game_build_id, set_id)
);

CREATE TABLE IF NOT EXISTS set_bonuses (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    set_id          INTEGER NOT NULL,
    num_pieces      INTEGER NOT NULL,      -- 2, 3, 4, 5 or 1 for mythic, 2 for monster
    effect_text     TEXT NOT NULL,         -- raw description
    effect_type     TEXT,                 -- optional: 'weapon_damage', 'crit', 'pen', etc.
    magnitude       REAL,                 -- optional for optimizer
    PRIMARY KEY (game_build_id, set_id, num_pieces),
    FOREIGN KEY (game_build_id, set_id) REFERENCES item_sets(game_build_id, set_id)
);

-- Which equipment slots this set can occupy (e.g. all body + weapons for craftable)
CREATE TABLE IF NOT EXISTS set_slots (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    set_id          INTEGER NOT NULL,
    slot_id         INTEGER NOT NULL REFERENCES equipment_slots(id),
    PRIMARY KEY (game_build_id, set_id, slot_id),
    FOREIGN KEY (game_build_id, set_id) REFERENCES item_sets(game_build_id, set_id)
);

-- ---------------------------------------------------------------------------
-- Skills / abilities (versioned per build; coefficients for damage formula)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    ability_id      INTEGER NOT NULL,
    name            TEXT NOT NULL,
    skill_line      TEXT,                 -- e.g. 'Herald of the Tome', 'Destruction Staff'
    skill_line_id   INTEGER,              -- game id if we have it
    class_name      TEXT,                 -- Arcanist, Sorcerer, etc. (NULL for weapon/guild)
    mechanic        TEXT,                 -- Magicka, Stamina, Ultimate, etc.
    description     TEXT,
    coefficient_json TEXT,                -- JSON array of {placeholder_index, equation_text, ratio?, duration?, tick?, dmg_type?}
    base_tooltip    REAL,                 -- reference tooltip at standard stats (Damage Skills xlsx)
    adps            REAL,                 -- adjusted DPS for DoTs (opportunity cost vs spammables)
    skill_damage_type TEXT,               -- e.g. 'ST Direct', 'AoE DoT', 'ST Direct + ST DoT'
    range_text      TEXT,                 -- e.g. '28m', '5m r'
    cost            INTEGER,              -- resource cost
    duration_sec    REAL,                 -- DoT/channel duration
    cast_time_sec   REAL,                 -- cast time (e.g. 0.8 for spammables)
    crux_required  INTEGER,               -- Arcanist builder/spender (nullable in practice)
    data_source    TEXT,                  -- e.g. 'damage_skills_u38_40', 'uesp_coef'
    update_label   TEXT,                  -- e.g. 'Update 39'
    PRIMARY KEY (game_build_id, ability_id)
);

-- ---------------------------------------------------------------------------
-- Buffs / debuffs (versioned per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buffs (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    buff_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_type     TEXT,                 -- e.g. 'Major Brutality', 'Minor Brittle'
    magnitude       REAL,
    duration_sec     REAL,
    effect_text     TEXT,
    PRIMARY KEY (game_build_id, buff_id)
);

-- ---------------------------------------------------------------------------
-- Mundus stones (versioned per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mundus_stones (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    mundus_id       INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_text     TEXT NOT NULL,
    effect_type     TEXT,                 -- e.g. 'crit_chance', 'weapon_damage'
    magnitude       REAL,
    PRIMARY KEY (game_build_id, mundus_id)
);

-- ---------------------------------------------------------------------------
-- Food / drink (versioned per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS foods (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    food_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,
    duration_sec    INTEGER,
    effect_text     TEXT,
    effect_json     TEXT,                -- JSON: {max_health, max_magicka, max_stamina, recovery_*}, etc.
    PRIMARY KEY (game_build_id, food_id)
);

-- ---------------------------------------------------------------------------
-- Potions (versioned per build)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS potions (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    potion_id       INTEGER NOT NULL,
    name            TEXT NOT NULL,
    duration_sec    REAL,
    cooldown_sec    REAL,
    effect_text     TEXT,
    effect_json     TEXT,                -- JSON: buffs granted, resource restore
    PRIMARY KEY (game_build_id, potion_id)
);

-- ---------------------------------------------------------------------------
-- Optimizer output: recommended builds per (build, class, role)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommended_builds (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    class_id            INTEGER NOT NULL REFERENCES classes(id),
    role_id             INTEGER NOT NULL REFERENCES roles(id),
    race_id             INTEGER NOT NULL REFERENCES races(id),
    mundus_id           INTEGER NOT NULL,
    food_id             INTEGER NOT NULL,
    potion_id           INTEGER NOT NULL,
    score_dps           REAL,             -- or score_hps / score_survival for healer/tank
    score_notes         TEXT,
    weapon_type         TEXT,             -- e.g. 'dw_nirn_precise', 'inferno_staff' (Weapon Comparisons)
    simulation_target_id INTEGER,         -- FK to simulation_targets (vet_dungeon_boss, trial_dummy_21m)
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_build_id, mundus_id) REFERENCES mundus_stones(game_build_id, mundus_id),
    FOREIGN KEY (game_build_id, food_id)   REFERENCES foods(game_build_id, food_id),
    FOREIGN KEY (game_build_id, potion_id)  REFERENCES potions(game_build_id, potion_id)
);

-- Which set is in which slot for a recommended build
CREATE TABLE IF NOT EXISTS recommended_build_equipment (
    recommended_build_id INTEGER NOT NULL REFERENCES recommended_builds(id) ON DELETE CASCADE,
    slot_id             INTEGER NOT NULL REFERENCES equipment_slots(id),
    set_id              INTEGER NOT NULL,
    game_build_id       INTEGER NOT NULL,  -- denormalized for FK; must match recommended_builds.game_build_id
    PRIMARY KEY (recommended_build_id, slot_id),
    FOREIGN KEY (game_build_id, set_id) REFERENCES item_sets(game_build_id, set_id)
);

-- ---------------------------------------------------------------------------
-- Optional: trials and bosses (for per-trial/per-boss overrides later)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS trial_bosses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id        INTEGER NOT NULL REFERENCES trials(id),
    name            TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Seed reference data (stable across patches)
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO set_types (id) VALUES
    ('crafted'), ('dungeon'), ('trial'), ('overland'), ('arena'), ('monster'), ('mythic'), ('pvp');

INSERT OR IGNORE INTO equipment_slots (id, name) VALUES
    (1, 'head'),
    (2, 'shoulders'),
    (3, 'chest'),
    (4, 'legs'),
    (5, 'feet'),
    (6, 'hands'),
    (7, 'waist'),
    (8, 'front_main'),
    (9, 'front_off'),
    (10, 'back_main'),
    (11, 'back_off');

INSERT OR IGNORE INTO classes (id, name) VALUES
    (1, 'Dragonknight'),
    (2, 'Sorcerer'),
    (3, 'Nightblade'),
    (4, 'Templar'),
    (5, 'Warden'),
    (6, 'Necromancer'),
    (7, 'Arcanist');

INSERT OR IGNORE INTO roles (id, name) VALUES
    (1, 'dd'),
    (2, 'healer'),
    (3, 'tank'),
    (4, 'support_dd');

-- Races (names only; effects go in race_effects per build)
INSERT OR IGNORE INTO races (id, name) VALUES
    (1, 'Altmer'),
    (2, 'Argonian'),
    (3, 'Bosmer'),
    (4, 'Breton'),
    (5, 'Dunmer'),
    (6, 'Imperial'),
    (7, 'Khajiit'),
    (8, 'Nord'),
    (9, 'Orc'),
    (10, 'Redguard');
