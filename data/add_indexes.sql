-- Performance indexes for player statistics queries
-- Run this after creating the database schema

-- Index on team_id for filtering by team
CREATE INDEX IF NOT EXISTS idx_player_boxscores_team_id ON player_boxscores(team_id);

-- Index on event_id for joining with games table
CREATE INDEX IF NOT EXISTS idx_player_boxscores_event_id ON player_boxscores(event_id);

-- Index on athlete_id for grouping player stats
CREATE INDEX IF NOT EXISTS idx_player_boxscores_athlete_id ON player_boxscores(athlete_id);

-- Composite index for team + event filtering (most selective)
CREATE INDEX IF NOT EXISTS idx_player_boxscores_team_event ON player_boxscores(team_id, event_id);
