-- Indexes for common queries (run after 01_schema.sql)

CREATE INDEX IF NOT EXISTS idx_set_summary_build_type ON set_summary(game_build_id, type);
CREATE INDEX IF NOT EXISTS idx_set_bonuses_build_game ON set_bonuses(game_build_id, game_id);
CREATE INDEX IF NOT EXISTS idx_skills_build_class ON skills(game_build_id, class_name);
CREATE INDEX IF NOT EXISTS idx_skills_build_line ON skills(game_build_id, skill_line);
CREATE INDEX IF NOT EXISTS idx_recommended_builds_build_class_role ON recommended_builds(game_build_id, class_id, role_id);
CREATE INDEX IF NOT EXISTS idx_race_effects_build ON race_effects(game_build_id, race_id);
