from pydantic import BaseModel
from typing import Optional


class PlayerBase(BaseModel):
    id: str
    uid: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    displayName: str
    shortName: Optional[str] = None
    weight: Optional[float] = None
    displayWeight: Optional[str] = None
    height: Optional[float] = None
    displayHeight: Optional[str] = None
    birthPlace_city: Optional[str] = None
    birthPlace_state: Optional[str] = None
    birthPlace_country: Optional[str] = None
    jersey: Optional[str] = None

    class Config:
        from_attributes = True


class PlayerResponse(PlayerBase):
    experience_years: Optional[int] = None
    experience_displayValue: Optional[str] = None
    hand_displayValue: Optional[str] = None


class PlayerSeasonResponse(BaseModel):
    season_player_id: str
    season: str
    player_id: str
    displayName: str
    position_abbreviation: Optional[str] = None
    position_name: Optional[str] = None
    team_id: str
    jersey: Optional[str] = None
    height: Optional[float] = None
    displayHeight: Optional[str] = None
    weight: Optional[float] = None
    displayWeight: Optional[str] = None
    experience_displayValue: Optional[str] = None
    headshot: Optional[str] = None

    class Config:
        from_attributes = True


class PlayerGameLog(BaseModel):
    event_id: str
    date: str
    opponent_id: str
    opponent_name: str
    is_home: bool
    MIN: Optional[str] = None
    PTS: Optional[str] = None
    REB: Optional[str] = None
    AST: Optional[str] = None
    FG: Optional[str] = None
    three_PT: Optional[str] = None
    FT: Optional[str] = None
    STL: Optional[str] = None
    BLK: Optional[str] = None
    TO: Optional[str] = None
    PF: Optional[str] = None

    class Config:
        from_attributes = True
