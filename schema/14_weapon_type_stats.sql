-- Weapon type stat bonuses. Source: Twin Blade and Blunt (Dual Wield passive) max rank from UESP.
-- When dual wielding different 1H types, effects from both apply at half strength (see core/weapon_type.py).
-- Other weapon types (2H, Bow, Staff) can be filled from Standalone Damage Modifiers Calculator xlsx.
-- Existing DBs created before bonus_penetration/bonus_crit_rating: run
--   python scripts/migrate_weapon_type_stats_columns.py [--db PATH]

-- Dual Wield (Twin Blade and Blunt II): per-weapon bonuses
INSERT OR REPLACE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'dagger', NULL, NULL, NULL, NULL, 657, 'Dual Wield passive: Critical Chance rating per dagger' FROM game_builds g;
INSERT OR REPLACE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'mace', NULL, NULL, NULL, 1487, NULL, 'Dual Wield passive: Offensive Penetration per mace' FROM game_builds g;
INSERT OR REPLACE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'sword', 129, NULL, NULL, NULL, NULL, 'Dual Wield passive: Weapon and Spell Damage per sword' FROM game_builds g;
INSERT OR REPLACE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'axe', NULL, NULL, 0.06, NULL, NULL, 'Dual Wield passive: Critical Damage done per axe (6%)' FROM game_builds g;

-- Placeholders for other weapon types (no bonuses until filled from xlsx or wiki)
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, '2h_sword', NULL, NULL, NULL, NULL, NULL, 'Two Handed line' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, '2h_axe', NULL, NULL, NULL, NULL, NULL, 'Two Handed line' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, '2h_mace', NULL, NULL, NULL, NULL, NULL, 'Two Handed line' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'bow', NULL, NULL, NULL, NULL, NULL, 'Bow line' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'inferno_staff', NULL, NULL, NULL, NULL, NULL, 'Destruction Staff' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'frost_staff', NULL, NULL, NULL, NULL, NULL, 'Destruction Staff' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'lightning_staff', NULL, NULL, NULL, NULL, NULL, 'Destruction Staff' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'resto_staff', NULL, NULL, NULL, NULL, NULL, 'Restoration Staff' FROM game_builds g;
INSERT OR IGNORE INTO weapon_type_stats (game_build_id, weapon_type, bonus_wd_sd, bonus_crit_chance, bonus_pct_done, bonus_penetration, bonus_crit_rating, notes) SELECT g.id, 'shield', NULL, NULL, NULL, NULL, NULL, 'One Hand and Shield' FROM game_builds g;
