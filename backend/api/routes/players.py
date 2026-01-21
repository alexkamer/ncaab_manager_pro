from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional

from core.database import get_db
from models.models import Player, PlayerSeason, PlayerBoxscore, Game
from schemas.player import PlayerResponse, PlayerSeasonResponse, PlayerGameLog
from core.config import settings

router = APIRouter()


@router.get("/", response_model=List[PlayerResponse])
def get_players(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0)
):
    """Get all players with optional filters"""
    query = db.query(Player)

    if search:
        query = query.filter(
            or_(
                Player.displayName.like(f"%{search}%"),
                Player.firstName.like(f"%{search}%"),
                Player.lastName.like(f"%{search}%")
            )
        )

    query = query.order_by(Player.displayName)
    players = query.offset(offset).limit(limit).all()

    return players


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: str,
    db: Session = Depends(get_db)
):
    """Get player details"""
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


@router.get("/{player_id}/seasons", response_model=List[PlayerSeasonResponse])
def get_player_seasons(
    player_id: str,
    db: Session = Depends(get_db)
):
    """Get all seasons for a player"""
    seasons = db.query(PlayerSeason).filter(
        PlayerSeason.player_id == player_id
    ).order_by(desc(PlayerSeason.season)).all()

    if not seasons:
        raise HTTPException(status_code=404, detail="No season data found for this player")

    return seasons


@router.get("/{player_id}/gamelog")
def get_player_gamelog(
    player_id: str,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get player game log for a season"""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get player stats joined with game info
    gamelog = db.query(
        PlayerBoxscore, Game
    ).join(
        Game, PlayerBoxscore.event_id == Game.id
    ).filter(
        and_(
            PlayerBoxscore.athlete_id == player_id,
            Game.season_year == season
        )
    ).order_by(desc(Game.date)).all()

    result = []
    for stat, game in gamelog:
        # Determine if home/away
        is_home = stat.team_id == game.home_team_id

        if is_home:
            opponent_id = game.away_team_id
            opponent_name = game.away_team_displayName
        else:
            opponent_id = game.home_team_id
            opponent_name = game.home_team_displayName

        result.append({
            "event_id": game.id,
            "date": game.date,
            "opponent_id": opponent_id,
            "opponent_name": opponent_name,
            "is_home": is_home,
            "MIN": stat.MIN,
            "PTS": stat.PTS,
            "REB": stat.REB,
            "AST": stat.AST,
            "FG": stat.FG,
            "three_PT": stat.three_PT,
            "FT": stat.FT,
            "STL": stat.STL,
            "BLK": stat.BLK,
            "TO": stat.TO,
            "PF": stat.PF
        })

    return result


@router.get("/{player_id}/stats")
def get_player_stats(
    player_id: str,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get aggregated player statistics for a season"""
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get all games for the season
    stats = db.query(PlayerBoxscore).join(
        Game, PlayerBoxscore.event_id == Game.id
    ).filter(
        and_(
            PlayerBoxscore.athlete_id == player_id,
            Game.season_year == season,
            Game.event_status_completed == 1
        )
    ).all()

    if not stats:
        return {
            "player_id": player_id,
            "season": season,
            "games_played": 0,
            "message": "No stats found for this season"
        }

    # Calculate aggregates
    games_played = len(stats)
    total_points = 0
    total_rebounds = 0
    total_assists = 0
    total_steals = 0
    total_blocks = 0
    total_turnovers = 0

    for stat in stats:
        try:
            total_points += int(stat.PTS) if stat.PTS else 0
            total_rebounds += int(stat.REB) if stat.REB else 0
            total_assists += int(stat.AST) if stat.AST else 0
            total_steals += int(stat.STL) if stat.STL else 0
            total_blocks += int(stat.BLK) if stat.BLK else 0
            total_turnovers += int(stat.TO) if stat.TO else 0
        except ValueError:
            continue

    return {
        "player_id": player_id,
        "season": season,
        "games_played": games_played,
        "points_per_game": round(total_points / games_played, 1),
        "rebounds_per_game": round(total_rebounds / games_played, 1),
        "assists_per_game": round(total_assists / games_played, 1),
        "steals_per_game": round(total_steals / games_played, 1),
        "blocks_per_game": round(total_blocks / games_played, 1),
        "turnovers_per_game": round(total_turnovers / games_played, 1),
        "total_points": total_points,
        "total_rebounds": total_rebounds,
        "total_assists": total_assists
    }
