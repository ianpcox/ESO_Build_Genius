-- =============================================================================
-- RACE EFFECTS (racial passives) – one row per passive per race per build.
-- Source: UESP wiki race pages (e.g. Online:High_Elf, Online:Breton).
-- Descriptions are max-rank (rank 3) where applicable.
-- =============================================================================

-- Altmer (race_id 1)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 1, 1, 'Increases your experience gain with the Destruction Staff skill line by 15%. Increases your experience gained by 1%.', 'Highborn', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 1, 2, 'When you activate an ability, you restore 625 Magicka or Stamina, based on whichever is lowest. This effect can occur once every 6 seconds. When you are using an ability with a channel or cast time, you take 5% less damage.', 'Spell Recharge', 625 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 1, 3, 'Increases your Max Magicka by 2000.', 'Syrabane''s Boon', 2000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 1, 4, 'Increases your Weapon and Spell Damage by 258.', 'Elemental Talent', 258 FROM game_builds g;

-- Argonian (race_id 2)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 2, 1, 'Increases your experience gain with the Restoration Staff skill line by 15%. Increases your swimming speed by 50%.', 'Amphibian', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 2, 2, 'Increases your healing done by 6%.', 'Life Mender', 0.06 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 2, 3, 'Increases your Max Health by 1000 and your Disease and Poison Resistance by 2310.', 'Argonian Resistance', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 2, 4, 'Increases your Max Magicka and Max Stamina by 1000. When you drink a potion, you restore 3125 Health, Magicka, and Stamina.', 'Resourceful', NULL FROM game_builds g;

-- Bosmer (race_id 3)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 3, 1, 'Increases your experience gain with the Bow skill line by 15%. Decreases your fall damage taken by 10%.', 'Acrobat', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 3, 2, 'Increases your Stealth Detection radius by 3 meters. Increases your Movement Speed by 5% and your Physical and Spell Penetration by 950.', 'Hunter''s Eye', 950 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 3, 3, 'Increases your Stamina Recovery by 258.', 'Y''ffre''s Endurance', 258 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 3, 4, 'Increases your Max Stamina by 2000 and your Disease and Poison Resistance by 2310.', 'Resist Affliction', NULL FROM game_builds g;

-- Breton (race_id 4)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 4, 1, 'Increases your experience gain with the Light Armor skill line by 15%. Increases your Alliance Points gained by 1%.', 'Opportunist', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 4, 2, 'Increases your Max Magicka by 2000.', 'Gift of Magnus', 2000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 4, 3, 'Increases your Spell Resistance by 2310. This effect is doubled if you are afflicted with Burning, Chilled, or Concussed. Increases your Magicka Recovery by 130.', 'Spell Attunement', 2310 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 4, 4, 'Reduces the Magicka cost of your abilities by 7%.', 'Magicka Mastery', 0.07 FROM game_builds g;

-- Dunmer (race_id 5)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 5, 1, 'Increases your experience gain with the Dual Wield skill line by 15%. Reduces your damage taken from environmental lava by 50%.', 'Ashlander', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 5, 2, 'Increases your Max Magicka and Max Stamina by 1910.', 'Dynamic', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 5, 3, 'Increases your Flame Resistance by 4620.', 'Resist Flame', 4620 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 5, 4, 'Increases your Weapon and Spell Damage by 258.', 'Ruination', 258 FROM game_builds g;

-- Imperial (race_id 6)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 6, 1, 'Increases your experience gain with the One Hand and Shield skill line by 15%. Increases your gold gained by 1%.', 'Diplomat', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 6, 2, 'Increases your Max Health by 2000.', 'Tough', 2000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 6, 3, 'Increases your Max Stamina by 2000.', 'Imperial Mettle', 2000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 6, 4, 'Reduces the cost of all your abilities by 6%.', 'Red Diamond', 0.06 FROM game_builds g;

-- Khajiit (race_id 7)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 7, 1, 'Increases your experience gain with the Medium Armor skill line by 15%. Increases your chance to successfully pickpocket by 5%.', 'Cutpurse', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 7, 2, 'Increases your Health, Magicka, and Stamina Recovery by 90.', 'Robustness', 90 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 7, 3, 'Increase your Maximum Health, Magicka, and Stamina by 915.', 'Lunar Blessings', 915 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 7, 4, 'Increases your Critical Damage and Critical Healing by 12%. Decreases your detection radius in Stealth by 3 meters.', 'Feline Ambush', 0.12 FROM game_builds g;

-- Nord (race_id 8)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 8, 1, 'Increases your experience gain with the Two Handed skill line by 15%. Increases the duration of any consumed drink by 15 minutes.', 'Reveler', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 8, 2, 'Increases your Max Health by 1000 and Frost Resistance by 4620.', 'Resist Frost', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 8, 3, 'Increases your Max Stamina by 1500. When you take damage, you gain 5 Ultimate. This effect can occur once every 10 seconds.', 'Stalwart', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 8, 4, 'Increases your Physical and Spell Resistance by 2600.', 'Rugged', 2600 FROM game_builds g;

-- Orc (race_id 9)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 9, 1, 'Increases your experience gain with the Heavy Armor skill line by 15%. Increases your crafting inspiration gained by 10%.', 'Craftsman', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 9, 2, 'Increases your Max Stamina by 1000.', 'Brawny', 1000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 9, 3, 'Increases your Max Health by 1000. When you deal damage, you heal for 2125 Health. This can occur once every 4 seconds.', 'Unflinching Rage', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 9, 4, 'Increases your Weapon and Spell Damage by 258. Reduces the cost of Sprint by 12% and increases the Movement Speed bonus of Sprint by 10%.', 'Swift Warrior', 258 FROM game_builds g;

-- Redguard (race_id 10)
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 10, 1, 'Increases your experience gain with the One Hand and Shield skill line by 15%. Increases the duration of any eaten food by 15 minutes.', 'Wayfarer', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 10, 2, 'Reduces the cost of your weapon abilities by 8%. Reduces the effectiveness of snares applied to you by 15%.', 'Martial Training', NULL FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 10, 3, 'Increases your Max Stamina by 2000.', 'Conditioning', 2000 FROM game_builds g;
INSERT OR REPLACE INTO race_effects (game_build_id, race_id, effect_ord, effect_text, effect_type, magnitude)
SELECT g.id, 10, 4, 'When you deal damage, you restore 1005 Stamina. This effect can occur once every 5 seconds.', 'Adrenaline Rush', 1005 FROM game_builds g;
