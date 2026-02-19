-- Trash packs and pack composition for AOE optimisation (per trial).
-- Pack composition and enemy types are filled from a standalone data source; this schema is ready for ingest.
-- Verification: ESO Log exportJson does not expose zone/encounter/npc tables; run scripts/verify_esolog_trials.py. See DATA_SOURCES.md.

-- =============================================================================
-- TRIAL TRASH PACKS (groups of enemies between boss encounters)
-- =============================================================================
CREATE TABLE IF NOT EXISTS trial_trash_packs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id        INTEGER NOT NULL REFERENCES trials(id),
    pack_ord        INTEGER NOT NULL,
    name            TEXT,
    notes           TEXT,
    UNIQUE (trial_id, pack_ord)
);

-- =============================================================================
-- TRIAL TRASH PACK ENEMIES (enemy types and count per pack)
-- =============================================================================
CREATE TABLE IF NOT EXISTS trial_trash_pack_enemies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id         INTEGER NOT NULL REFERENCES trial_trash_packs(id) ON DELETE CASCADE,
    enemy_name      TEXT NOT NULL,
    count_val       INTEGER NOT NULL DEFAULT 1,
    UNIQUE (pack_id, enemy_name)
);

CREATE INDEX IF NOT EXISTS idx_trial_trash_packs_trial ON trial_trash_packs(trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_trash_pack_enemies_pack ON trial_trash_pack_enemies(pack_id);

-- =============================================================================
-- SEED: one placeholder trash pack per trial (pack composition to be filled from standalone source)
-- =============================================================================
INSERT OR IGNORE INTO trial_trash_packs (id, trial_id, pack_ord, name, notes) VALUES
    (1, 1, 1, 'Cloudrest trash', 'Placeholder; fill composition from standalone source'),
    (2, 2, 1, 'Sunspire trash', 'Placeholder; fill composition from standalone source'),
    (3, 3, 1, 'Rockgrove trash', 'Placeholder; fill composition from standalone source'),
    (4, 4, 1, 'Dreadsail Reef trash', 'Placeholder; fill composition from standalone source'),
    (5, 5, 1, 'Sanity''s Edge trash', 'Placeholder; fill composition from standalone source'),
    (6, 6, 1, 'Aetherian Archive trash', 'Placeholder; fill composition from standalone source'),
    (7, 7, 1, 'Hel Ra Citadel trash', 'Placeholder; fill composition from standalone source'),
    (8, 8, 1, 'Sanctum Ophidia trash', 'Placeholder; fill composition from standalone source'),
    (9, 9, 1, 'Maw of Lorkhaj trash', 'Placeholder; fill composition from standalone source'),
    (10, 10, 1, 'Halls of Fabrication trash', 'Placeholder; fill composition from standalone source'),
    (11, 11, 1, 'Asylum Sanctorium trash', 'Placeholder; fill composition from standalone source'),
    (12, 12, 1, 'Kyne''s Aegis trash', 'Placeholder; fill composition from standalone source'),
    (13, 13, 1, 'Ossein Cage trash', 'Placeholder; fill composition from standalone source'),
    (14, 14, 1, 'Lucent Citadel trash', 'Placeholder; fill composition from standalone source');

-- Example enemy row per pack (generic); replace with real composition when source available
INSERT OR IGNORE INTO trial_trash_pack_enemies (pack_id, enemy_name, count_val) VALUES
    (1, 'Generic trash', 1),
    (2, 'Generic trash', 1),
    (3, 'Generic trash', 1),
    (4, 'Generic trash', 1),
    (5, 'Generic trash', 1),
    (6, 'Generic trash', 1),
    (7, 'Generic trash', 1),
    (8, 'Generic trash', 1),
    (9, 'Generic trash', 1),
    (10, 'Generic trash', 1),
    (11, 'Generic trash', 1),
    (12, 'Generic trash', 1),
    (13, 'Generic trash', 1),
    (14, 'Generic trash', 1);
