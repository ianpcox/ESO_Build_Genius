-- Seed class skill lines (21 = 3 per class) and minimal buff catalog for every existing game_build.
-- Ensures a 'Default' game_build exists if none do. Seeds one example set (Kinras's Wrath) and
-- buff_grants_set_bonus for the first game_build so duplicate-buff logic is testable.

-- =============================================================================
-- Ensure at least one game build exists
-- =============================================================================
INSERT OR IGNORE INTO game_builds (label) VALUES ('Default');

-- =============================================================================
-- Class skill lines (21): 3 per class. skill_line_id 1xx = DK, 2xx = Sorc, 3xx = NB, 4xx = Templar, 5xx = Warden, 6xx = Necro, 7xx = Arcanist
-- Insert for every game_build so ingest-created builds get lines too (re-run create_db after ingest to backfill).
-- =============================================================================
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id)
SELECT g.id, 101, 'Ardent Flame', 'class', 1 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 102, 'Draconic Power', 'class', 1 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 103, 'Earthen Heart', 'class', 1 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 201, 'Dark Magic', 'class', 2 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 202, 'Daedric Summoning', 'class', 2 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 203, 'Storm Calling', 'class', 2 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 301, 'Assassination', 'class', 3 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 302, 'Shadow', 'class', 3 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 303, 'Siphon', 'class', 3 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 401, 'Dawn''s Wrath', 'class', 4 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 402, 'Restoring Light', 'class', 4 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 403, 'Aedric Spear', 'class', 4 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 501, 'Animal Companion', 'class', 5 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 502, 'Green Balance', 'class', 5 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 503, 'Winter''s Embrace', 'class', 5 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 601, 'Bone Tyrant', 'class', 6 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 602, 'Grave Lord', 'class', 6 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 603, 'Living Death', 'class', 6 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 701, 'Curative Runeforms', 'class', 7 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 702, 'Herald of the Tome', 'class', 7 FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 703, 'Soldier of Apocrypha', 'class', 7 FROM game_builds g;

-- =============================================================================
-- Minimal buff catalog (common Major/Minor buffs). Insert for every game_build.
-- buff_id 1 = Minor Berserk, 2 = Major Berserk, etc.
-- =============================================================================
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 1, 'Minor Berserk', 'damage_done', 0.05, NULL, 'Increases damage done by 5%' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 2, 'Major Berserk', 'damage_done', 0.10, NULL, 'Increases damage done by 10%' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 3, 'Minor Brutality', 'weapon_spell_damage', NULL, NULL, 'Increases Weapon and Spell Damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 4, 'Major Brutality', 'weapon_spell_damage', NULL, NULL, 'Increases Weapon and Spell Damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 5, 'Minor Force', 'critical_damage', 0.10, NULL, 'Increases critical damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 6, 'Major Force', 'critical_damage', 0.25, NULL, 'Increases critical damage' FROM game_builds g;

-- =============================================================================
-- Example set and set bonus for first game_build (Kinras 5pc = Minor Berserk)
-- so buff_grants_set_bonus is testable.
-- =============================================================================
INSERT OR IGNORE INTO item_sets (game_build_id, set_id, name, set_type, max_pieces)
SELECT (SELECT id FROM game_builds ORDER BY id LIMIT 1), 1, 'Kinras''s Wrath', 'trial', 5;
INSERT OR IGNORE INTO set_bonuses (game_build_id, set_id, num_pieces, effect_text, effect_type, magnitude)
SELECT (SELECT id FROM game_builds ORDER BY id LIMIT 1), 1, 5, 'When you deal Critical Damage, you gain Minor Berserk', 'damage_done', 0.05;
INSERT OR IGNORE INTO buff_grants_set_bonus (game_build_id, buff_id, set_id, num_pieces)
SELECT (SELECT id FROM game_builds ORDER BY id LIMIT 1), 1, 1, 5;
