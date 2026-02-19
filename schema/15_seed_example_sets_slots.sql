-- set_item_slots for example sets so the optimizer can run without full UESP ingest.
-- Kinras (1) and a second 5pc (2) get all slots; monster (3) gets head+shoulders only.

-- Kinras (game_id=1): all 14 slots (only for game_builds that have this set, e.g. from 07)
INSERT OR IGNORE INTO set_item_slots (game_build_id, game_id, slot_id)
SELECT g.id, 1, 1 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 2 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 3 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 4 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 5 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 6 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 7 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 8 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 9 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 10 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 11 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 12 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 13 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1)
UNION ALL SELECT g.id, 1, 14 FROM game_builds g WHERE EXISTS (SELECT 1 FROM set_summary s WHERE s.game_build_id = g.id AND s.game_id = 1);

-- Second 5pc set (example) and monster set for optimizer demo
INSERT OR IGNORE INTO set_summary (game_build_id, game_id, set_name, type, set_max_equip_count)
SELECT g.id, 2, 'Example 5pc', 'dungeon', 5 FROM game_builds g;
INSERT OR IGNORE INTO set_summary (game_build_id, game_id, set_name, type, set_max_equip_count)
SELECT g.id, 3, 'Example Monster', 'monster', 2 FROM game_builds g;

INSERT OR IGNORE INTO set_item_slots (game_build_id, game_id, slot_id)
SELECT g.id, 2, 1 FROM game_builds g
UNION ALL SELECT g.id, 2, 2 FROM game_builds g
UNION ALL SELECT g.id, 2, 3 FROM game_builds g
UNION ALL SELECT g.id, 2, 4 FROM game_builds g
UNION ALL SELECT g.id, 2, 5 FROM game_builds g
UNION ALL SELECT g.id, 2, 6 FROM game_builds g
UNION ALL SELECT g.id, 2, 7 FROM game_builds g
UNION ALL SELECT g.id, 2, 8 FROM game_builds g
UNION ALL SELECT g.id, 2, 9 FROM game_builds g
UNION ALL SELECT g.id, 2, 10 FROM game_builds g
UNION ALL SELECT g.id, 2, 11 FROM game_builds g
UNION ALL SELECT g.id, 2, 12 FROM game_builds g
UNION ALL SELECT g.id, 2, 13 FROM game_builds g
UNION ALL SELECT g.id, 2, 14 FROM game_builds g;

INSERT OR IGNORE INTO set_item_slots (game_build_id, game_id, slot_id)
SELECT g.id, 3, 1 FROM game_builds g
UNION ALL SELECT g.id, 3, 2 FROM game_builds g;
