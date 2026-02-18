-- Weapon, guild, and world skill lines (non-class). Used when linking skills from xlsx class sheets.
-- Ids 801+ to avoid clashing with class lines (101-703).

INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id)
SELECT g.id, 801, 'Destruction Staff', 'weapon', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 802, 'Two Handed', 'weapon', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 803, 'Dual Wield', 'weapon', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 804, 'Bow', 'weapon', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 805, 'Fighters Guild', 'guild', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 806, 'Mages Guild', 'guild', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 807, 'Undaunted', 'guild', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 808, 'Soul Magic', 'world', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 809, 'Psijic Order', 'guild', NULL FROM game_builds g;
INSERT OR IGNORE INTO skill_lines (game_build_id, skill_line_id, name, skill_line_type, class_id) SELECT g.id, 810, 'Assault', 'guild', NULL FROM game_builds g;
