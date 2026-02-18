-- Schema additions driven by Damage Skills xlsx, Kilt cheat sheet, Standalone Damage Modifiers Calculator, and UESP Build Editor.
-- Run after 02_indexes.sql.

-- ---------------------------------------------------------------------------
-- Simulation target (resistance, pen, etc.) for damage formula
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulation_targets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    resistance      INTEGER NOT NULL DEFAULT 18200,
    crit_resist_pct REAL DEFAULT 0,
    flat_crit_resist INTEGER DEFAULT 0,
    penetration_pct REAL DEFAULT 0,
    flat_penetration INTEGER DEFAULT 0,
    notes           TEXT
);

INSERT OR IGNORE INTO simulation_targets (id, name, resistance, notes) VALUES
    (1, 'vet_dungeon_boss', 18200, 'Default PvE vet dungeon boss'),
    (2, 'trial_dummy_21m', 18200, '21M Iron Atronach trial dummy');

-- ---------------------------------------------------------------------------
-- Stat modifier reference (References for Stats, Set Bonus Comparisons)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stat_modifier_reference (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    category        TEXT NOT NULL,
    name            TEXT NOT NULL,
    base_value      REAL,
    effective_value  REAL,
    formula_notes   TEXT,
    PRIMARY KEY (game_build_id, category, name)
);

-- ---------------------------------------------------------------------------
-- Weapon type stat bonuses (Weapon Comparisons sheet)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weapon_type_stats (
    game_build_id       INTEGER NOT NULL REFERENCES game_builds(id),
    weapon_type         TEXT NOT NULL,
    bonus_wd_sd         REAL,
    bonus_crit_chance   REAL,
    bonus_pct_done      REAL,
    notes               TEXT,
    PRIMARY KEY (game_build_id, weapon_type)
);

-- ---------------------------------------------------------------------------
-- Trial/boss set notes (e.g. Harpooner's Wading Kilt cheat sheet)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trial_boss_set_notes (
    trial_id        INTEGER REFERENCES trials(id),
    boss_name       TEXT NOT NULL,
    set_id          INTEGER NOT NULL,
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    note_type       TEXT NOT NULL,
    note_text       TEXT,
    PRIMARY KEY (trial_id, boss_name, set_id, game_build_id),
    FOREIGN KEY (game_build_id, set_id) REFERENCES item_sets(game_build_id, set_id)
);

-- New columns on skills and recommended_builds are defined in 01_schema.sql
-- (base_tooltip, adps, skill_damage_type, range_text, cost, duration_sec, cast_time_sec,
--  crux_required, data_source, update_label on skills; weapon_type, simulation_target_id on recommended_builds).
-- If your DB was created before that update, add them manually or run a one-off migration.
