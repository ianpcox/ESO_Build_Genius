-- Seed traits (weapon/armor/jewelry), glyphs (UESP Online:Glyphs), and common weapon poisons.
-- Insert glyphs and weapon_poisons for every game_build.

-- =============================================================================
-- TRAITS (id, name, slot_type)
-- Weapon 1-9, Armor 10-17, Jewelry 18-26
-- =============================================================================
INSERT OR IGNORE INTO traits (id, name, slot_type) VALUES
    (1, 'Precise', 'weapon'), (2, 'Sharpened', 'weapon'), (3, 'Powered', 'weapon'),
    (4, 'Charged', 'weapon'), (5, 'Infused', 'weapon'), (6, 'Defending', 'weapon'),
    (7, 'Training', 'weapon'), (8, 'Weighted', 'weapon'), (9, 'Nirnhoned', 'weapon');
INSERT OR IGNORE INTO traits (id, name, slot_type) VALUES
    (10, 'Divines', 'armor'), (11, 'Reinforced', 'armor'), (12, 'Sturdy', 'armor'),
    (13, 'Well Fitted', 'armor'), (14, 'Infused', 'armor'), (15, 'Impenetrable', 'armor'),
    (16, 'Nirnhoned', 'armor'), (17, 'Training', 'armor');
INSERT OR IGNORE INTO traits (id, name, slot_type) VALUES
    (18, 'Healthy', 'jewelry'), (19, 'Arcane', 'jewelry'), (20, 'Robust', 'jewelry'),
    (21, 'Bloodthirsty', 'jewelry'), (22, 'Harmony', 'jewelry'), (23, 'Infused', 'jewelry'),
    (24, 'Triune', 'jewelry'), (25, 'Protective', 'jewelry'), (26, 'Swift', 'jewelry');

-- =============================================================================
-- WEAPON GLYPHS (glyph_id 1-14; source UESP Online:Glyphs)
-- =============================================================================
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 1, 'Glyph of Flame', 'Deals X Fire Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 2, 'Glyph of Shock', 'Deals X Shock Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 3, 'Glyph of Frost', 'Deals X Frost Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 4, 'Glyph of Poison', 'Deals X Poison Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 5, 'Glyph of Foulness', 'Deals X Disease Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 6, 'Glyph of Decrease Health', 'Deals X Oblivion Damage', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 7, 'Glyph of Weapon Damage', 'Increase Weapon and Spell Damage by X for 5 seconds', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 8, 'Glyph of Absorb Health', 'Deals X Magic Damage and recovers Y Health', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 9, 'Glyph of Absorb Magicka', 'Deals X Magic Damage and recovers Y Magicka', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 10, 'Glyph of Absorb Stamina', 'Deals X Physical Damage and recovers Y Stamina', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 11, 'Glyph of Crushing', 'Reduce target Physical and Spell Resistance by X for 5 seconds', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 12, 'Glyph of Weakening', 'Reduce target Weapon and Spell Damage by X for 5 seconds', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 13, 'Glyph of Hardening', 'Grants X point Damage Shield for 5 seconds', 'weapon' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 14, 'Glyph of Prismatic Onslaught', 'Deals X Magic Damage, recovers Y Health, Z Magicka and Stamina', 'weapon' FROM game_builds g;

-- =============================================================================
-- ARMOR GLYPHS (glyph_id 20-23)
-- =============================================================================
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 20, 'Glyph of Health', 'Adds X Maximum Health', 'armor' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 21, 'Glyph of Magicka', 'Adds X Maximum Magicka', 'armor' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 22, 'Glyph of Stamina', 'Adds X Maximum Stamina', 'armor' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 23, 'Glyph of Prismatic Defense', 'Adds X Maximum Health, Magicka and Stamina', 'armor' FROM game_builds g;

-- =============================================================================
-- JEWELRY GLYPHS (glyph_id 30-33; common DD/healer picks)
-- =============================================================================
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 30, 'Glyph of Increase Physical Harm', 'Adds X Weapon and Spell Damage and Stamina Recovery', 'jewelry' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 31, 'Glyph of Increase Magical Harm', 'Adds X Spell and Weapon Damage and Magicka Recovery', 'jewelry' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 32, 'Glyph of Magicka Recovery', 'Adds X Magicka Recovery', 'jewelry' FROM game_builds g;
INSERT OR IGNORE INTO glyphs (game_build_id, glyph_id, name, effect_text, slot_kind)
SELECT g.id, 33, 'Glyph of Stamina Recovery', 'Adds X Stamina Recovery', 'jewelry' FROM game_builds g;

-- =============================================================================
-- WEAPON POISONS (common choices)
-- =============================================================================
INSERT OR IGNORE INTO weapon_poisons (game_build_id, poison_id, name, effect_text, duration_sec)
SELECT g.id, 1, 'Ravage Health Poison', 'Deals X Damage and reduces healing received', 4.0 FROM game_builds g;
INSERT OR IGNORE INTO weapon_poisons (game_build_id, poison_id, name, effect_text, duration_sec)
SELECT g.id, 2, 'Damage Health Poison', 'Deals X Poison Damage', 4.0 FROM game_builds g;
INSERT OR IGNORE INTO weapon_poisons (game_build_id, poison_id, name, effect_text, duration_sec)
SELECT g.id, 3, 'Vulnerability Poison', 'Increases damage taken by X%', 4.0 FROM game_builds g;
INSERT OR IGNORE INTO weapon_poisons (game_build_id, poison_id, name, effect_text, duration_sec)
SELECT g.id, 4, 'No weapon poison', 'No poison applied', NULL FROM game_builds g;

-- =============================================================================
-- effect_json for weapon glyphs and poisons (tradeoff: enchants vs poisons)
-- Approximate CP 160 values; weapon glyphs proc ~4s CD; poisons on LA/HA.
-- =============================================================================
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"fire"}' WHERE slot_kind = 'weapon' AND glyph_id = 1;
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"shock"}' WHERE slot_kind = 'weapon' AND glyph_id = 2;
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"frost"}' WHERE slot_kind = 'weapon' AND glyph_id = 3;
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"poison"}' WHERE slot_kind = 'weapon' AND glyph_id = 4;
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"disease"}' WHERE slot_kind = 'weapon' AND glyph_id = 5;
UPDATE glyphs SET effect_json = '{"type":"damage","damage":645,"cooldown_sec":4,"damage_type":"oblivion"}' WHERE slot_kind = 'weapon' AND glyph_id = 6;
UPDATE glyphs SET effect_json = '{"type":"buff","stat":"weapon_spell_damage","amount":258,"duration_sec":5,"cooldown_sec":5}' WHERE slot_kind = 'weapon' AND glyph_id = 7;
UPDATE glyphs SET effect_json = '{"type":"absorb","damage":400,"heal":400,"cooldown_sec":4}' WHERE slot_kind = 'weapon' AND glyph_id = 8;
UPDATE glyphs SET effect_json = '{"type":"absorb","damage":400,"resource":"magicka","amount":400,"cooldown_sec":4}' WHERE slot_kind = 'weapon' AND glyph_id = 9;
UPDATE glyphs SET effect_json = '{"type":"absorb","damage":400,"resource":"stamina","amount":400,"cooldown_sec":4}' WHERE slot_kind = 'weapon' AND glyph_id = 10;
UPDATE glyphs SET effect_json = '{"type":"debuff","stat":"resistance","amount":2108,"duration_sec":5,"cooldown_sec":5}' WHERE slot_kind = 'weapon' AND glyph_id = 11;
UPDATE glyphs SET effect_json = '{"type":"debuff","stat":"weapon_spell_damage","amount":-258,"duration_sec":5,"cooldown_sec":5}' WHERE slot_kind = 'weapon' AND glyph_id = 12;
UPDATE glyphs SET effect_json = '{"type":"shield","amount":5000,"duration_sec":5,"cooldown_sec":5}' WHERE slot_kind = 'weapon' AND glyph_id = 13;
UPDATE glyphs SET effect_json = '{"type":"prismatic","damage":300,"heal":300,"magicka":300,"stamina":300,"cooldown_sec":4}' WHERE slot_kind = 'weapon' AND glyph_id = 14;
UPDATE weapon_poisons SET effect_json = '{"type":"dot","damage":1200,"duration_sec":4,"healing_received_debuff":true}' WHERE poison_id = 1;
UPDATE weapon_poisons SET effect_json = '{"type":"dot","damage":1400,"duration_sec":4}' WHERE poison_id = 2;
UPDATE weapon_poisons SET effect_json = '{"type":"debuff","damage_taken_pct":0.10,"duration_sec":4}' WHERE poison_id = 3;
