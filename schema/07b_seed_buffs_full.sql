-- Extended buff catalog for set-bonus parsing. buff_id 1-6 are in 07_seed_skill_lines_and_buffs.sql.
-- Insert for every game_build so buff_grants_set_bonus can reference these by name when parsing set_bonus_desc.
-- =============================================================================

-- Vulnerability (debuff applied by sets to enemies)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 7, 'Major Vulnerability', 'damage_taken', 0.10, NULL, 'Increases damage taken by 10%' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 8, 'Minor Vulnerability', 'damage_taken', 0.05, NULL, 'Increases damage taken by 5%' FROM game_builds g;
-- Aegis
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 9, 'Minor Aegis', 'damage_taken', 0.05, NULL, 'Reduces damage from Dungeon, Trial, Arena monsters' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 10, 'Major Aegis', 'damage_taken', NULL, NULL, 'Reduces damage from Dungeon, Trial, Arena monsters' FROM game_builds g;
-- Slayer
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 11, 'Minor Slayer', 'damage_done', 0.05, NULL, 'Increases damage to Dungeon, Trial, Arena monsters' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 12, 'Major Slayer', 'damage_done', 0.10, NULL, 'Increases damage to Dungeon, Trial, Arena monsters' FROM game_builds g;
-- Courage (named set bonus)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 13, 'Major Courage', 'weapon_spell_damage', NULL, NULL, 'Increases Weapon and Spell Damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 14, 'Minor Courage', 'weapon_spell_damage', NULL, NULL, 'Increases Weapon and Spell Damage' FROM game_builds g;
-- Protection
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 15, 'Major Protection', 'damage_taken', 0.10, NULL, 'Reduces damage taken by 10%' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 16, 'Minor Protection', 'damage_taken', 0.05, NULL, 'Reduces damage taken by 5%' FROM game_builds g;
-- Expedition
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 17, 'Major Expedition', 'movement_speed', NULL, NULL, 'Increases movement speed' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 18, 'Minor Expedition', 'movement_speed', NULL, NULL, 'Increases movement speed' FROM game_builds g;
-- Vitality
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 19, 'Minor Vitality', 'healing_received', NULL, NULL, 'Increases healing received' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 20, 'Major Vitality', 'healing_received', NULL, NULL, 'Increases healing received' FROM game_builds g;
-- Timidity (e.g. Monomyth)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 21, 'Minor Timidity', 'damage_done', NULL, NULL, 'Reduces damage done' FROM game_builds g;
-- Resolve
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 22, 'Minor Resolve', 'physical_resistance', NULL, NULL, 'Increases Physical Resistance' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 23, 'Major Resolve', 'physical_resistance', NULL, NULL, 'Increases Physical Resistance' FROM game_builds g;
-- Evasion
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 24, 'Minor Evasion', 'dodge', NULL, NULL, 'Increases chance to avoid damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 25, 'Major Evasion', 'dodge', NULL, NULL, 'Increases chance to avoid damage' FROM game_builds g;
-- Endurance
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 26, 'Minor Endurance', 'stamina_recovery', NULL, NULL, 'Increases Stamina Recovery' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 27, 'Major Endurance', 'stamina_recovery', NULL, NULL, 'Increases Stamina Recovery' FROM game_builds g;
-- Intellect
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 28, 'Minor Intellect', 'magicka_recovery', NULL, NULL, 'Increases Magicka Recovery' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 29, 'Major Intellect', 'magicka_recovery', NULL, NULL, 'Increases Magicka Recovery' FROM game_builds g;
-- Fortitude
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 30, 'Minor Fortitude', 'health_recovery', NULL, NULL, 'Increases Health Recovery' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 31, 'Major Fortitude', 'health_recovery', NULL, NULL, 'Increases Health Recovery' FROM game_builds g;
-- Mending
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 32, 'Minor Mending', 'healing_done', NULL, NULL, 'Increases healing done' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 33, 'Major Mending', 'healing_done', NULL, NULL, 'Increases healing done' FROM game_builds g;
-- Prophecy / Savagery (crit)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 34, 'Minor Prophecy', 'critical_rating', NULL, NULL, 'Increases Spell Critical' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 35, 'Major Prophecy', 'critical_rating', NULL, NULL, 'Increases Spell Critical' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 36, 'Minor Savagery', 'critical_rating', NULL, NULL, 'Increases Weapon Critical' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 37, 'Major Savagery', 'critical_rating', NULL, NULL, 'Increases Weapon Critical' FROM game_builds g;
-- Sorcery (already have Minor/Major Brutality 3,4 - weapon/spell damage; Sorcery is spell-specific)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 38, 'Minor Sorcery', 'spell_damage', NULL, NULL, 'Increases Spell Damage' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 39, 'Major Sorcery', 'spell_damage', NULL, NULL, 'Increases Spell Damage' FROM game_builds g;
-- Breach (armor debuff applied by sets)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 40, 'Major Breach', 'armor_reduction', NULL, NULL, 'Reduces target Armor' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 41, 'Minor Breach', 'armor_reduction', NULL, NULL, 'Reduces target Armor' FROM game_builds g;
-- Heroism (ultimate gen)
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 42, 'Minor Heroism', 'ultimate_gain', NULL, NULL, 'Increases Ultimate gain' FROM game_builds g;
INSERT OR IGNORE INTO buffs (game_build_id, buff_id, name, effect_type, magnitude, duration_sec, effect_text)
SELECT g.id, 43, 'Major Heroism', 'ultimate_gain', NULL, NULL, 'Increases Ultimate gain' FROM game_builds g;
