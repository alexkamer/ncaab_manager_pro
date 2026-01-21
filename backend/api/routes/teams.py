from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_, and_, desc
from typing import List, Optional
import json

from core.database import get_db
from models.models import Team, Game, PlayerSeason
from schemas.team import TeamResponse, TeamScheduleGame, TeamRoster, TeamWithStats
from core.config import settings

router = APIRouter()


@router.get("/", response_model=List[TeamResponse])
def get_teams(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or location"),
    conference: Optional[str] = Query(None, description="Filter by conference slug"),
    limit: int = Query(100, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0)
):
    """Get all teams with optional filters"""
    query = db.query(Team)

    if search:
        query = query.filter(
            or_(
                Team.displayName.like(f"%{search}%"),
                Team.location.like(f"%{search}%"),
                Team.nickname.like(f"%{search}%")
            )
        )

    # Order by display name
    query = query.order_by(Team.displayName)

    teams = query.offset(offset).limit(limit).all()
    return teams


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    db: Session = Depends(get_db)
):
    """Get team details"""
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return team


@router.get("/{team_id}/schedule")
def get_team_schedule(
    team_id: str,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get team schedule for a season"""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get games where team is either home or away
    games = db.query(Game).filter(
        and_(
            Game.season_year == season,
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
        )
    ).order_by(Game.date).all()

    schedule = []
    for game in games:
        is_home = game.home_team_id == team_id

        if is_home:
            opponent_id = game.away_team_id
            opponent_name = game.away_team_displayName
            opponent_abbr = game.away_team_abbreviation
            score = game.home_team_score
            opponent_score = game.away_team_score
            won = game.home_team_winner == 1 if game.home_team_winner is not None else None
        else:
            opponent_id = game.home_team_id
            opponent_name = game.home_team_displayName
            opponent_abbr = game.home_team_abbreviation
            score = game.away_team_score
            opponent_score = game.home_team_score
            won = game.away_team_winner == 1 if game.away_team_winner is not None else None

        schedule.append({
            "id": game.id,
            "date": game.date,
            "opponent_id": opponent_id,
            "opponent_name": opponent_name,
            "opponent_abbreviation": opponent_abbr,
            "is_home": is_home,
            "is_conference": game.is_conference_competition == 1,
            "score": score,
            "opponent_score": opponent_score,
            "won": won,
            "completed": game.event_status_completed == 1,
            "status_detail": game.event_status_detail
        })

    return schedule


@router.get("/{team_id}/roster")
def get_team_roster(
    team_id: str,
    season: str = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get team roster for a season"""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    roster = db.query(PlayerSeason).filter(
        and_(
            PlayerSeason.team_id == team_id,
            PlayerSeason.season == season
        )
    ).order_by(PlayerSeason.displayName).all()

    return roster


@router.get("/{team_id}/stats")
def get_team_stats(
    team_id: str,
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get team statistics for a season"""
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get completed games
    games = db.query(Game).filter(
        and_(
            Game.season_year == season,
            Game.event_status_completed == 1,
            or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
        )
    ).all()

    # Calculate stats
    wins = 0
    losses = 0
    conf_wins = 0
    conf_losses = 0
    points_for = 0
    points_against = 0
    home_wins = 0
    away_wins = 0
    home_games = 0
    away_games = 0

    for game in games:
        is_home = game.home_team_id == team_id
        is_conference = game.is_conference_competition == 1

        if is_home:
            won = game.home_team_winner == 1
            score = game.home_team_score or 0
            opp_score = game.away_team_score or 0
            home_games += 1
        else:
            won = game.away_team_winner == 1
            score = game.away_team_score or 0
            opp_score = game.home_team_score or 0
            away_games += 1

        if won:
            wins += 1
            if is_home:
                home_wins += 1
            else:
                away_wins += 1
            if is_conference:
                conf_wins += 1
        else:
            losses += 1
            if is_conference:
                conf_losses += 1

        points_for += score
        points_against += opp_score

    total_games = len(games)
    ppg = round(points_for / total_games, 1) if total_games > 0 else 0
    opp_ppg = round(points_against / total_games, 1) if total_games > 0 else 0

    return {
        "team_id": team_id,
        "season": season,
        "wins": wins,
        "losses": losses,
        "win_percentage": round(wins / total_games, 3) if total_games > 0 else 0,
        "conference_wins": conf_wins,
        "conference_losses": conf_losses,
        "home_record": f"{home_wins}-{home_games - home_wins}",
        "away_record": f"{away_wins}-{away_games - away_wins}",
        "points_per_game": ppg,
        "opponent_points_per_game": opp_ppg,
        "point_differential": round(ppg - opp_ppg, 1),
        "total_games": total_games
    }
