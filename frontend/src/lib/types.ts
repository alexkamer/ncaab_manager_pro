export interface Game {
  id: string;
  uid: string;
  season_year: number;
  season_type: number;
  week?: number;
  date: string;
  is_neutral_site: number;
  is_conference_competition: number;
  event_status_name?: string;
  event_status_state?: string;
  event_status_completed: number;
  event_status_detail?: string;
  event_status_short_detail?: string;
  home_team_id: string;
  home_team_displayName: string;
  home_team_abbreviation: string;
  home_team_score?: number;
  home_team_winner?: number;
  home_team_color?: string;
  home_team_logo?: string;
  away_team_id: string;
  away_team_displayName: string;
  away_team_abbreviation: string;
  away_team_score?: number;
  away_team_winner?: number;
  away_team_color?: string;
  away_team_logo?: string;
}

export interface Team {
  id: string;
  uid: string;
  slug?: string;
  abbreviation: string;
  displayName: string;
  name: string;
  nickname?: string;
  location: string;
  color?: string;
  alternateColor?: string;
  logos?: string;
}

export interface Player {
  id: string;
  uid: string;
  firstName?: string;
  lastName?: string;
  displayName: string;
  shortName?: string;
  weight?: number;
  displayWeight?: string;
  height?: number;
  displayHeight?: string;
  birthPlace_city?: string;
  birthPlace_state?: string;
  birthPlace_country?: string;
  jersey?: string;
  experience_years?: number;
  experience_displayValue?: string;
}

export interface TeamStats {
  team_id: string;
  season: number;
  wins: number;
  losses: number;
  win_percentage: number;
  conference_wins: number;
  conference_losses: number;
  home_record: string;
  away_record: string;
  points_per_game: number;
  opponent_points_per_game: number;
  point_differential: number;
  total_games: number;
}

export interface PlayerStats {
  player_id: string;
  season: number;
  games_played: number;
  points_per_game: number;
  rebounds_per_game: number;
  assists_per_game: number;
  steals_per_game: number;
  blocks_per_game: number;
  turnovers_per_game: number;
  total_points: number;
  total_rebounds: number;
  total_assists: number;
}

export interface Prediction {
  event_id: string;
  name?: string;
  short_name?: string;
  homeTeam_team_id: string;
  homeTeam_gameProjection?: number;
  homeTeam_gameProjection_display?: string;
  homeTeam_teamChanceLoss?: number;
  awayTeam_team_id: string;
  awayTeam_gameProjection?: number;
  awayTeam_gameProjection_display?: string;
  awayTeam_teamChanceLoss?: number;
}

export interface Odds {
  event_provider_id: string;
  event_id: string;
  provider_id: string;
  provider_name: string;
  over_under?: number;
  spread?: number;
  over_odds?: number;
  under_odds?: number;
  away_team_moneyline?: number;
  away_team_spread?: string;
  home_team_moneyline?: number;
  home_team_spread?: string;
}

export interface PowerRanking {
  rank: number;
  team_id: string;
  team_name: string;
  abbreviation: string;
  wins: number;
  losses: number;
  win_percentage: number;
  color?: string;
  alternateColor?: string;
}
