from pydantic import BaseModel
from typing import Optional, List


class TeamBase(BaseModel):
    id: str
    uid: str
    slug: Optional[str] = None
    abbreviation: str
    displayName: str
    name: str
    nickname: Optional[str] = None
    location: str
    color: Optional[str] = None
    alternateColor: Optional[str] = None
    logos: Optional[str] = None

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    pass


class TeamWithStats(TeamBase):
    wins: int = 0
    losses: int = 0
    conference_wins: int = 0
    conference_losses: int = 0
    current_streak: Optional[str] = None
    last_game_date: Optional[str] = None


class TeamScheduleGame(BaseModel):
    id: str
    date: str
    opponent_id: str
    opponent_name: str
    opponent_abbreviation: str
    is_home: bool
    is_conference: bool
    score: Optional[int] = None
    opponent_score: Optional[int] = None
    won: Optional[bool] = None
    completed: bool
    status_detail: Optional[str] = None

    class Config:
        from_attributes = True


class TeamRoster(BaseModel):
    season: str
    player_id: str
    displayName: str
    position_abbreviation: Optional[str] = None
    jersey: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    experience_displayValue: Optional[str] = None

    class Config:
        from_attributes = True
