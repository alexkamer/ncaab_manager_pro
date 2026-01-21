from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case, text
from typing import List, Optional
from datetime import datetime, timedelta

from core.database import get_db
from models.models import Game, Ranking, Team, Prediction, Odds
from core.config import settings

router = APIRouter()


@router.get("/power-rankings")
def get_power_rankings(
    season: int = Query(..., description="Season year"),
    week: Optional[int] = Query(None, description="Week number"),
    limit: int = Query(25, le=100),
    db: Session = Depends(get_db)
):
    """Get power rankings based on win percentage and strength of schedule"""
    # For now, calculate simple win percentage rankings
    # TODO: Add more sophisticated ranking algorithm

    # Subquery to get wins
    wins_subq = db.query(
        case(
            (Game.home_team_id == Team.id, Game.home_team_id),
            (Game.away_team_id == Team.id, Game.away_team_id)
        ).label('team_id'),
        func.count(Game.id).label('wins')
    ).filter(
        and_(
            Game.season_year == season,
            Game.event_status_completed == 1,
            or_(
                and_(Game.home_team_id == Team.id, Game.home_team_winner == 1),
                and_(Game.away_team_id == Team.id, Game.away_team_winner == 1)
            )
        )
    ).group_by('team_id').subquery()

    # Subquery to get total games
    games_subq = db.query(
        case(
            (Game.home_team_id == Team.id, Game.home_team_id),
            (Game.away_team_id == Team.id, Game.away_team_id)
        ).label('team_id'),
        func.count(Game.id).label('total_games')
    ).filter(
        and_(
            Game.season_year == season,
            Game.event_status_completed == 1
        )
    ).group_by('team_id').subquery()

    # Get teams with their records
    teams = db.query(
        Team.id,
        Team.displayName,
        Team.abbreviation,
        Team.color,
        Team.alternateColor
    ).all()

    rankings = []
    for team in teams:
        wins = db.execute(
            text(f"SELECT COUNT(*) FROM games WHERE season_year = {season} "
            f"AND event_status_completed = 1 "
            f"AND ((home_team_id = '{team.id}' AND home_team_winner = 1) "
            f"OR (away_team_id = '{team.id}' AND away_team_winner = 1))")
        ).scalar()

        total = db.execute(
            text(f"SELECT COUNT(*) FROM games WHERE season_year = {season} "
            f"AND event_status_completed = 1 "
            f"AND (home_team_id = '{team.id}' OR away_team_id = '{team.id}')")
        ).scalar()

        if total > 0:
            win_pct = wins / total
            rankings.append({
                "team_id": team.id,
                "team_name": team.displayName,
                "abbreviation": team.abbreviation,
                "wins": wins,
                "losses": total - wins,
                "win_percentage": round(win_pct, 3),
                "color": team.color,
                "alternateColor": team.alternateColor
            })

    # Sort by win percentage
    rankings.sort(key=lambda x: x['win_percentage'], reverse=True)

    # Add ranking
    for i, team in enumerate(rankings[:limit]):
        team['rank'] = i + 1

    return rankings[:limit]


@router.get("/ap-poll")
def get_ap_poll(
    season: int = Query(..., description="Season year"),
    week: Optional[int] = Query(None, description="Week number"),
    db: Session = Depends(get_db)
):
    """Get AP Poll rankings"""
    query = db.query(Ranking, Team).join(
        Team, Ranking.team_id == Team.id
    ).filter(
        and_(
            Ranking.season == str(season),
            Ranking.ranking_provider_name.like("%AP%")
        )
    )

    if week:
        query = query.filter(Ranking.week == week)
    else:
        # Get latest week
        latest_week = db.query(func.max(Ranking.week)).filter(
            and_(
                Ranking.season == str(season),
                Ranking.ranking_provider_name.like("%AP%")
            )
        ).scalar()
        query = query.filter(Ranking.week == latest_week)

    rankings = query.order_by(Ranking.current_rank).all()

    result = []
    for ranking, team in rankings:
        result.append({
            "rank": ranking.current_rank,
            "previous_rank": ranking.previous_rank,
            "team_id": team.id,
            "team_name": team.displayName,
            "record": ranking.record_summary,
            "points": ranking.points,
            "first_place_votes": ranking.first_place_votes,
            "trend": ranking.trend,
            "week": ranking.week
        })

    return result


@router.get("/conference-standings")
def get_conference_standings(
    conference: str = Query(..., description="Conference slug"),
    season: int = Query(..., description="Season year"),
    db: Session = Depends(get_db)
):
    """Get conference standings"""
    # Get all teams in the conference
    teams_in_conf = db.query(Game.home_team_id).filter(
        and_(
            Game.season_year == season,
            Game.home_team_conference_slug == conference
        )
    ).distinct().all()

    team_ids = [t[0] for t in teams_in_conf]

    standings = []
    for team_id in team_ids:
        # Get team info
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            continue

        # Calculate conference record
        conf_games = db.query(Game).filter(
            and_(
                Game.season_year == season,
                Game.event_status_completed == 1,
                Game.is_conference_competition == 1,
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )
        ).all()

        conf_wins = 0
        conf_losses = 0
        for game in conf_games:
            if game.home_team_id == team_id:
                if game.home_team_winner == 1:
                    conf_wins += 1
                else:
                    conf_losses += 1
            else:
                if game.away_team_winner == 1:
                    conf_wins += 1
                else:
                    conf_losses += 1

        # Calculate overall record
        all_games = db.query(Game).filter(
            and_(
                Game.season_year == season,
                Game.event_status_completed == 1,
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )
        ).all()

        overall_wins = 0
        overall_losses = 0
        for game in all_games:
            if game.home_team_id == team_id:
                if game.home_team_winner == 1:
                    overall_wins += 1
                else:
                    overall_losses += 1
            else:
                if game.away_team_winner == 1:
                    overall_wins += 1
                else:
                    overall_losses += 1

        conf_win_pct = conf_wins / (conf_wins + conf_losses) if (conf_wins + conf_losses) > 0 else 0

        standings.append({
            "team_id": team.id,
            "team_name": team.displayName,
            "abbreviation": team.abbreviation,
            "conference_wins": conf_wins,
            "conference_losses": conf_losses,
            "conference_win_pct": round(conf_win_pct, 3),
            "overall_wins": overall_wins,
            "overall_losses": overall_losses
        })

    # Sort by conference win percentage
    standings.sort(key=lambda x: x['conference_win_pct'], reverse=True)

    # Add rank
    for i, team in enumerate(standings):
        team['rank'] = i + 1

    return standings


@router.get("/betting-edges")
def get_betting_edges(
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    min_edge: float = Query(5.0, description="Minimum edge percentage"),
    db: Session = Depends(get_db)
):
    """Find games where prediction disagrees with betting line"""
    query = db.query(Game, Prediction, Odds).join(
        Prediction, Game.id == Prediction.event_id
    ).join(
        Odds, Game.id == Odds.event_id
    ).filter(
        Game.event_status_completed == 0
    )

    if date:
        query = query.filter(Game.date.like(f"{date}%"))
    else:
        # Default to upcoming games
        today = datetime.now().strftime("%Y-%m-%d")
        query = query.filter(Game.date >= today)

    results = query.all()

    edges = []
    for game, prediction, odds in results:
        # Calculate implied probability from moneyline
        if odds.home_team_moneyline and odds.away_team_moneyline:
            home_implied = (
                abs(odds.home_team_moneyline) / (abs(odds.home_team_moneyline) + 100) * 100
                if odds.home_team_moneyline < 0
                else 100 / (odds.home_team_moneyline + 100) * 100
            )

            # Compare with prediction
            if prediction.homeTeam_gameProjection:
                pred_home_pct = prediction.homeTeam_gameProjection * 100
                edge = abs(pred_home_pct - home_implied)

                if edge >= min_edge:
                    edges.append({
                        "game_id": game.id,
                        "date": game.date,
                        "home_team": game.home_team_displayName,
                        "away_team": game.away_team_displayName,
                        "prediction_home_win_pct": round(pred_home_pct, 1),
                        "implied_home_win_pct": round(home_implied, 1),
                        "edge": round(edge, 1),
                        "recommended_bet": "home" if pred_home_pct > home_implied else "away",
                        "home_moneyline": odds.home_team_moneyline,
                        "away_moneyline": odds.away_team_moneyline
                    })

    # Sort by edge
    edges.sort(key=lambda x: x['edge'], reverse=True)

    return edges
