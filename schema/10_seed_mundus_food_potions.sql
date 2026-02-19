-- Seed mundus stones (from UESP wiki Online:Mundus_Stones), plus minimal food and potion
-- so recommended_builds FKs are satisfied. Insert for every existing game_build.
-- Mundus IDs 1-13 match a canonical order; effect values are base (no Divines).

-- =============================================================================
-- MUNDUS STONES (13; source: https://en.uesp.net/wiki/Online:Mundus_Stones)
-- =============================================================================
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 1, 'The Apprentice', 'Increases Spell Damage', 'spell_damage', 238 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 2, 'The Atronach', 'Increases Magicka Recovery', 'magicka_recovery', 310 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 3, 'The Lady', 'Increases Physical and Spell Resistance', 'resistance', 2744 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 4, 'The Lord', 'Increases Maximum Health', 'max_health', 2225 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 5, 'The Lover', 'Increases Physical and Spell Penetration', 'penetration', 2744 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 6, 'The Mage', 'Increases Maximum Magicka', 'max_magicka', 2023 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 7, 'The Ritual', 'Increases Healing Done', 'healing_done', 0.08 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 8, 'The Serpent', 'Increases Stamina Recovery', 'stamina_recovery', 310 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 9, 'The Shadow', 'Increases Critical Damage and Healing done', 'critical_damage', 0.11 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 10, 'The Steed', 'Increases Health Recovery and Movement Speed', 'health_recovery_movement', 238 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 11, 'The Thief', 'Increases Weapon and Spell Critical Strike ratings', 'critical_rating', 1212 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 12, 'The Tower', 'Increases Maximum Stamina', 'max_stamina', 2023 FROM game_builds g;
INSERT OR IGNORE INTO mundus_stones (game_build_id, mundus_id, name, effect_text, effect_type, magnitude)
SELECT g.id, 13, 'The Warrior', 'Increases Weapon Damage', 'weapon_damage', 238 FROM game_builds g;

-- =============================================================================
-- MINIMAL FOOD (1) and POTION (1) so recommended_builds can reference them
-- Expand via ingest script or addon export later.
-- =============================================================================
INSERT OR IGNORE INTO foods (game_build_id, food_id, name, duration_sec, effect_text, effect_json)
SELECT g.id, 1, 'Artaeum Takeaway Broth', 7200, 'Increases Max Health, Max Magicka, Max Stamina, and Health Recovery', NULL FROM game_builds g;
INSERT OR IGNORE INTO foods (game_build_id, food_id, name, duration_sec, effect_text, effect_json)
SELECT g.id, 2, 'Clockwork Citrus Filet', 7200, 'Increases Max Health, Max Magicka, Max Stamina, and Magicka Recovery', NULL FROM game_builds g;
INSERT OR IGNORE INTO foods (game_build_id, food_id, name, duration_sec, effect_text, effect_json)
SELECT g.id, 3, 'Ghastly Eye Bowl', 7200, 'Increases Max Health, Max Magicka, Max Stamina, and Stamina Recovery', NULL FROM game_builds g;

INSERT OR IGNORE INTO potions (game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_text, effect_json)
SELECT g.id, 1, 'Essence of Weapon Power', 47.5, 45, 'Restore Health, Magicka, Stamina; Major Brutality, Major Sorcery, Major Savagery', NULL FROM game_builds g;
INSERT OR IGNORE INTO potions (game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_text, effect_json)
SELECT g.id, 2, 'Essence of Spell Power', 47.5, 45, 'Restore Health, Magicka, Stamina; Major Prophecy, Major Sorcery, Major Savagery', NULL FROM game_builds g;
INSERT OR IGNORE INTO potions (game_build_id, potion_id, name, duration_sec, cooldown_sec, effect_text, effect_json)
SELECT g.id, 3, 'Essence of Health', 47.5, 45, 'Restore Health, Magicka, Stamina', NULL FROM game_builds g;
