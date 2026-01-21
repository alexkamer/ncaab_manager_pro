from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamInfo(BaseModel):
    id: str
    displayName: str
    abbreviation: str
    location: str
    name: str
    color: Optional[str] = None
    alternateColor: Optional[str] = None
    logo: Optional[str] = None
    conference_slug: Optional[str] = None

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    id: str
    uid: str
    season_year: int
    season_type: int
    week: Optional[int] = None
    date: str
    is_neutral_site: int
    is_conference_competition: int
    event_status_name: Optional[str] = None
    event_status_state: Optional[str] = None
    event_status_completed: int
    event_status_detail: Optional[str] = None
    event_status_short_detail: Optional[str] = None

    class Config:
        from_attributes = True


class GameSummary(GameBase):
    home_team_id: str
    home_team_displayName: str
    home_team_abbreviation: str
    home_team_score: Optional[int] = None
    home_team_winner: Optional[int] = None
    home_team_color: Optional[str] = None
    home_team_logo: Optional[str] = None

    away_team_id: str
    away_team_displayName: str
    away_team_abbreviation: str
    away_team_score: Optional[int] = None
    away_team_winner: Optional[int] = None
    away_team_color: Optional[str] = None
    away_team_logo: Optional[str] = None


class GameDetail(GameBase):
    game_note: Optional[str] = None
    timeValid: int
    venue_id: Optional[str] = None
    attendance: Optional[int] = None
    officials: Optional[str] = None

    home_team_id: str
    home_team_winner: Optional[int] = None
    home_team_score: Optional[int] = None
    home_linescores: Optional[str] = None
    home_team_records: Optional[str] = None
    home_team_location: str
    home_team_name: str
    home_team_abbreviation: str
    home_team_nickname: str
    home_team_displayName: str
    home_team_color: Optional[str] = None
    home_team_alternate_color: Optional[str] = None
    home_team_logos: Optional[str] = None
    home_team_conference_id: Optional[str] = None
    home_team_conference_slug: Optional[str] = None

    away_team_id: str
    away_team_winner: Optional[int] = None
    away_team_score: Optional[int] = None
    away_linescores: Optional[str] = None
    away_team_records: Optional[str] = None
    away_team_location: str
    away_team_name: str
    away_team_abbreviation: str
    away_team_nickname: str
    away_team_displayName: str
    away_team_color: Optional[str] = None
    away_team_alternate_color: Optional[str] = None
    away_team_logos: Optional[str] = None
    away_team_conference_id: Optional[str] = None
    away_team_conference_slug: Optional[str] = None


class TeamBoxscoreResponse(BaseModel):
    event_team_id: str
    event_id: str
    team_id: str
    home_away: str
    fieldGoalsMade: Optional[str] = None
    fieldGoalsAttempted: Optional[str] = None
    fieldGoalPct: Optional[str] = None
    threePointFieldGoalsMade: Optional[str] = None
    threePointFieldGoalsAttempted: Optional[str] = None
    threePointFieldGoalPct: Optional[str] = None
    freeThrowsMade: Optional[str] = None
    freeThrowsAttempted: Optional[str] = None
    freeThrowPct: Optional[str] = None
    totalRebounds: Optional[str] = None
    offensiveRebounds: Optional[str] = None
    defensiveRebounds: Optional[str] = None
    assists: Optional[str] = None
    steals: Optional[str] = None
    blocks: Optional[str] = None
    turnovers: Optional[str] = None
    fouls: Optional[str] = None
    largestLead: Optional[str] = None

    class Config:
        from_attributes = True


class PlayerBoxscoreResponse(BaseModel):
    event_athlete_id: str
    athlete_id: str
    athlete_name: str
    athlete_position_abbreviation: Optional[str] = None
    athlete_jersey: Optional[str] = None
    athlete_starter: int
    MIN: Optional[str] = None
    FG: Optional[str] = None
    three_PT: Optional[str] = None
    FT: Optional[str] = None
    REB: Optional[str] = None
    AST: Optional[str] = None
    STL: Optional[str] = None
    BLK: Optional[str] = None
    TO: Optional[str] = None
    PF: Optional[str] = None
    PTS: Optional[str] = None

    class Config:
        from_attributes = True


class GameBoxscore(BaseModel):
    game: GameDetail
    team_stats: List[TeamBoxscoreResponse]
    player_stats: List[PlayerBoxscoreResponse]


class PredictionResponse(BaseModel):
    event_id: str
    name: Optional[str] = None
    short_name: Optional[str] = None
    homeTeam_team_id: str
    homeTeam_gameProjection: Optional[float] = None
    homeTeam_gameProjection_display: Optional[str] = None
    homeTeam_teamChanceLoss: Optional[float] = None
    awayTeam_team_id: str
    awayTeam_gameProjection: Optional[float] = None
    awayTeam_gameProjection_display: Optional[str] = None
    awayTeam_teamChanceLoss: Optional[float] = None

    class Config:
        from_attributes = True


class OddsResponse(BaseModel):
    event_provider_id: str
    event_id: str
    provider_id: str
    provider_name: str
    over_under: Optional[float] = None
    spread: Optional[float] = None
    over_odds: Optional[int] = None
    under_odds: Optional[int] = None
    away_team_moneyline: Optional[int] = None
    away_team_spread: Optional[str] = None
    home_team_moneyline: Optional[int] = None
    home_team_spread: Optional[str] = None

    class Config:
        from_attributes = True
