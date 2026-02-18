-- Skill lines (class, weapon, guild, world, scribed), class ownership, passives,
-- standalone buffs/debuffs linked to skill lines and passives, target granularity,
-- and subclassing (base class + 3 class-line slots, up to 2 replaceable with other classes).

-- =============================================================================
-- SKILL LINE TYPES (lookup)
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_line_types (
    id              TEXT PRIMARY KEY   -- 'class', 'weapon', 'guild', 'world', 'scribed'
);

-- =============================================================================
-- SKILL LINES (per game build)
-- Class lines: exactly 3 per class, class_id set. Weapon/guild/world/scribed: class_id NULL.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_lines (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    skill_line_id   INTEGER NOT NULL,
    name            TEXT NOT NULL,
    skill_line_type TEXT NOT NULL REFERENCES skill_line_types(id),
    class_id        INTEGER NULL REFERENCES classes(id),   -- only for type = 'class'
    PRIMARY KEY (game_build_id, skill_line_id),
    CHECK (skill_line_type != 'class' OR class_id IS NOT NULL)
);

-- =============================================================================
-- SKILL LINE PASSIVES (per line, per build)
-- Passives that belong to a skill line; can grant buffs (see buff_grants).
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_line_passives (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    skill_line_id   INTEGER NOT NULL,
    passive_ord     INTEGER NOT NULL,
    name            TEXT NOT NULL,
    effect_text     TEXT,
    effect_type     TEXT,
    magnitude       REAL,
    PRIMARY KEY (game_build_id, skill_line_id, passive_ord),
    FOREIGN KEY (game_build_id, skill_line_id) REFERENCES skill_lines(game_build_id, skill_line_id)
);

-- =============================================================================
-- SKILLS -> SKILL LINES (skills already exist; ensure skill_line_id points here)
-- skills.skill_line_id now references skill_lines.skill_line_id (same game_build_id).
-- =============================================================================
-- No schema change if skills.skill_line_id already exists; application ensures
-- it matches skill_lines.skill_line_id for the same game_build_id.

-- =============================================================================
-- TARGET TYPES (lookup) – granularity for "vs. Undead", "vs. Daedra", etc.
-- =============================================================================
CREATE TABLE IF NOT EXISTS target_types (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

-- =============================================================================
-- SKILL TARGET BONUS – which target types a skill applies to or gets bonus vs.
-- Use for skills that have different effect or bonus vs. Undead, Daedra, etc.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_target_bonus (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    ability_id      INTEGER NOT NULL,
    target_type_id  INTEGER NOT NULL REFERENCES target_types(id),
    effect_text     TEXT,               -- e.g. "Bonus damage vs Undead"
    magnitude       REAL,               -- optional numeric bonus
    PRIMARY KEY (game_build_id, ability_id, target_type_id),
    FOREIGN KEY (game_build_id, ability_id) REFERENCES skills(game_build_id, ability_id)
);

-- =============================================================================
-- BUFF GRANTS – standalone buffs linked to skill lines and their passives (or abilities)
-- One row per (buff, source): either an ability grants the buff, or a passive in a line does.
-- =============================================================================
CREATE TABLE IF NOT EXISTS buff_grants (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    buff_id         INTEGER NOT NULL,
    grant_type      TEXT NOT NULL CHECK (grant_type IN ('ability', 'passive')),
    ability_id      INTEGER NULL,      -- set when grant_type = 'ability'
    skill_line_id   INTEGER NULL,      -- set when grant_type = 'passive'; or context when ability
    passive_ord     INTEGER NULL,      -- set when grant_type = 'passive'
    FOREIGN KEY (game_build_id, buff_id) REFERENCES buffs(game_build_id, buff_id),
    FOREIGN KEY (game_build_id, skill_line_id) REFERENCES skill_lines(game_build_id, skill_line_id),
    CHECK (
        (grant_type = 'ability' AND ability_id IS NOT NULL) OR
        (grant_type = 'passive' AND skill_line_id IS NOT NULL AND passive_ord IS NOT NULL)
    ),
    PRIMARY KEY (game_build_id, buff_id, grant_type, ability_id, skill_line_id, passive_ord)
);

-- =============================================================================
-- SUBCLASSING: which 3 class skill lines a build uses
-- Base class (recommended_builds.class_id) has 3 class lines; build can REPLACE
-- up to 2 of them with class lines from up to 2 other classes.
-- Example: Necromancer keeps Grave Lord; replaces Bone Tyrant with Nightblade Assassination,
--          replaces Living Death with Arcanist Herald of the Tome.
-- Constraint (enforced in app): at most 2 of the 3 slots have skill_lines.class_id != build class_id.
-- =============================================================================
CREATE TABLE IF NOT EXISTS recommended_build_class_lines (
    recommended_build_id INTEGER NOT NULL REFERENCES recommended_builds(id) ON DELETE CASCADE,
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    slot_ord            INTEGER NOT NULL CHECK (slot_ord >= 1 AND slot_ord <= 3),
    skill_line_id       INTEGER NOT NULL,
    PRIMARY KEY (recommended_build_id, slot_ord),
    FOREIGN KEY (game_build_id, skill_line_id) REFERENCES skill_lines(game_build_id, skill_line_id),
    UNIQUE (recommended_build_id, slot_ord)
);

-- =============================================================================
-- SEED: skill line types and target types
-- =============================================================================
INSERT OR IGNORE INTO skill_line_types (id) VALUES
    ('class'), ('weapon'), ('guild'), ('world'), ('scribed');

INSERT OR IGNORE INTO target_types (id, name) VALUES
    (1, 'Any'),
    (2, 'Undead'),
    (3, 'Daedra'),
    (4, 'Humanoid'),
    (5, 'Beast'),
    (6, 'Construct'),
    (7, 'Player');

-- Indexes for skill lines, passives, buff grants, and subclassing
CREATE INDEX IF NOT EXISTS idx_skill_lines_build_type ON skill_lines(game_build_id, skill_line_type);
CREATE INDEX IF NOT EXISTS idx_skill_lines_build_class ON skill_lines(game_build_id, class_id);
CREATE INDEX IF NOT EXISTS idx_skill_line_passives_line ON skill_line_passives(game_build_id, skill_line_id);
CREATE INDEX IF NOT EXISTS idx_buff_grants_buff ON buff_grants(game_build_id, buff_id);
CREATE INDEX IF NOT EXISTS idx_buff_grants_line ON buff_grants(game_build_id, skill_line_id);
CREATE INDEX IF NOT EXISTS idx_recommended_build_class_lines_build ON recommended_build_class_lines(recommended_build_id);
