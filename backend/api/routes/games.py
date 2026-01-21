from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime
import json

from core.database import get_db
from models.models import Game, TeamBoxscore, PlayerBoxscore, Prediction, Odds
from schemas.game import (
    GameSummary, GameDetail, GameBoxscore,
    TeamBoxscoreResponse, PlayerBoxscoreResponse,
    PredictionResponse, OddsResponse
)
from core.config import settings

router = APIRouter()


@router.get("/", response_model=List[GameSummary])
def get_games(
    db: Session = Depends(get_db),
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    season: Optional[int] = Query(None, description="Season year"),
    team_id: Optional[str] = Query(None, description="Team ID"),
    conference: Optional[str] = Query(None, description="Conference slug"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    limit: int = Query(50, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0)
):
    """Get games with optional filters"""
    query = db.query(Game)

    # Apply filters
    if date:
        query = query.filter(Game.date.like(f"{date}%"))

    if season:
        query = query.filter(Game.season_year == season)

    if team_id:
        query = query.filter(
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
        )

    if conference:
        query = query.filter(
            or_(
                Game.home_team_conference_slug == conference,
                Game.away_team_conference_slug == conference
            )
        )

    if completed is not None:
        query = query.filter(Game.event_status_completed == (1 if completed else 0))

    # Order by date descending (most recent first)
    query = query.order_by(desc(Game.date))

    # Pagination
    games = query.offset(offset).limit(limit).all()

    # Parse logos for each game
    result = []
    for game in games:
        game_dict = game.__dict__.copy()

        # Parse home team logo
        if game.home_team_logos:
            try:
                logos = json.loads(game.home_team_logos)
                game_dict['home_team_logo'] = logos[0]['href'] if logos else None
            except:
                game_dict['home_team_logo'] = None
        else:
            game_dict['home_team_logo'] = None

        # Parse away team logo
        if game.away_team_logos:
            try:
                logos = json.loads(game.away_team_logos)
                game_dict['away_team_logo'] = logos[0]['href'] if logos else None
            except:
                game_dict['away_team_logo'] = None
        else:
            game_dict['away_team_logo'] = None

        result.append(GameSummary(**game_dict))

    return result


@router.get("/today", response_model=List[GameSummary])
def get_today_games(
    db: Session = Depends(get_db)
):
    """Get today's games"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Query today's games directly
    query = db.query(Game)
    query = query.filter(Game.date.like(f"{today}%"))
    query = query.order_by(desc(Game.date))
    games = query.limit(50).all()

    # Parse logos for each game
    result = []
    for game in games:
        game_dict = game.__dict__.copy()

        # Parse home team logo
        if game.home_team_logos:
            try:
                logos = json.loads(game.home_team_logos)
                game_dict['home_team_logo'] = logos[0]['href'] if logos else None
            except:
                game_dict['home_team_logo'] = None
        else:
            game_dict['home_team_logo'] = None

        # Parse away team logo
        if game.away_team_logos:
            try:
                logos = json.loads(game.away_team_logos)
                game_dict['away_team_logo'] = logos[0]['href'] if logos else None
            except:
                game_dict['away_team_logo'] = None
        else:
            game_dict['away_team_logo'] = None

        result.append(GameSummary(**game_dict))

    return result


@router.get("/{game_id}", response_model=GameDetail)
def get_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed game information"""
    game = db.query(Game).filter(Game.id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return game


@router.get("/{game_id}/boxscore")
def get_game_boxscore(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get full boxscore for a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    team_stats = db.query(TeamBoxscore).filter(
        TeamBoxscore.event_id == game_id
    ).all()

    player_stats = db.query(PlayerBoxscore).filter(
        PlayerBoxscore.event_id == game_id
    ).order_by(
        PlayerBoxscore.athlete_starter.desc(),
        PlayerBoxscore.PTS.desc()
    ).all()

    return {
        "game": game,
        "team_stats": team_stats,
        "player_stats": player_stats
    }


@router.get("/{game_id}/predictions", response_model=PredictionResponse)
def get_game_predictions(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get predictions for a game"""
    prediction = db.query(Prediction).filter(
        Prediction.event_id == game_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found for this game")

    return prediction


@router.get("/{game_id}/odds", response_model=List[OddsResponse])
def get_game_odds(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get odds from all providers for a game"""
    odds = db.query(Odds).filter(
        Odds.event_id == game_id
    ).all()

    if not odds:
        raise HTTPException(status_code=404, detail="No odds found for this game")

    return odds
