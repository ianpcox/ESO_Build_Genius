-- Link buffs to set bonuses so we can detect duplicate buff sources.
-- Optimization: avoid recommending sets that only add a buff already provided by
-- skills/passives (e.g. Combat Prayer = Minor Berserk; Kinras 5pc = Minor Berserk => redundant).

-- =============================================================================
-- BUFF GRANTS FROM SET BONUSES
-- Which set bonus (set_id + num_pieces) grants which buff. Use with buff_grants
-- (ability/passive) to get all sources of a buff for a build.
-- =============================================================================
CREATE TABLE IF NOT EXISTS buff_grants_set_bonus (
    game_build_id   INTEGER NOT NULL REFERENCES game_builds(id),
    buff_id         INTEGER NOT NULL,
    set_id          INTEGER NOT NULL,
    num_pieces      INTEGER NOT NULL,
    PRIMARY KEY (game_build_id, buff_id, set_id, num_pieces),
    FOREIGN KEY (game_build_id, buff_id) REFERENCES buffs(game_build_id, buff_id),
    FOREIGN KEY (game_build_id, set_id) REFERENCES item_sets(game_build_id, set_id)
);

CREATE INDEX IF NOT EXISTS idx_buff_grants_set_bonus_buff ON buff_grants_set_bonus(game_build_id, buff_id);
CREATE INDEX IF NOT EXISTS idx_buff_grants_set_bonus_set ON buff_grants_set_bonus(game_build_id, set_id);
