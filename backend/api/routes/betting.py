from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from models.models import Odds, Game
from schemas.game import OddsResponse

router = APIRouter()


@router.get("/lines")
def get_betting_lines(
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    provider: Optional[str] = Query(None, description="Sportsbook provider name"),
    db: Session = Depends(get_db)
):
    """Get betting lines for games"""
    query = db.query(Odds, Game).join(
        Game, Odds.event_id == Game.id
    )

    if date:
        query = query.filter(Game.date.like(f"{date}%"))
    else:
        # Default to today
        today = datetime.now().strftime("%Y-%m-%d")
        query = query.filter(Game.date.like(f"{today}%"))

    if provider:
        query = query.filter(Odds.provider_name.like(f"%{provider}%"))

    query = query.order_by(Game.date)
    results = query.all()

    lines = []
    for odds, game in results:
        lines.append({
            "event_id": game.id,
            "date": game.date,
            "home_team": game.home_team_displayName,
            "away_team": game.away_team_displayName,
            "provider": odds.provider_name,
            "spread": odds.spread,
            "over_under": odds.over_under,
            "home_moneyline": odds.home_team_moneyline,
            "away_moneyline": odds.away_team_moneyline,
            "home_spread": odds.home_team_spread,
            "away_spread": odds.away_team_spread,
            "home_spread_odds": odds.home_team_spread_odds,
            "away_spread_odds": odds.away_team_spread_odds,
            "over_odds": odds.over_odds,
            "under_odds": odds.under_odds
        })

    return lines


@router.get("/movers")
def get_line_movers(
    hours: int = Query(24, description="Time window in hours"),
    min_movement: float = Query(2.0, description="Minimum line movement"),
    db: Session = Depends(get_db)
):
    """Get games with significant line movement"""
    # This is a placeholder - would need historical odds data to implement properly
    # For now, return empty list
    return {
        "message": "Line movement tracking requires historical odds data",
        "movers": []
    }


@router.get("/providers")
def get_sportsbook_providers(
    db: Session = Depends(get_db)
):
    """Get list of sportsbook providers in database"""
    providers = db.query(
        Odds.provider_id,
        Odds.provider_name
    ).distinct().all()

    return [
        {"provider_id": p.provider_id, "provider_name": p.provider_name}
        for p in providers
    ]


@router.get("/compare/{game_id}")
def compare_sportsbooks(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Compare odds across all sportsbooks for a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    odds = db.query(Odds).filter(Odds.event_id == game_id).all()

    if not odds:
        raise HTTPException(status_code=404, detail="No odds found for this game")

    comparison = {
        "game_id": game.id,
        "home_team": game.home_team_displayName,
        "away_team": game.away_team_displayName,
        "date": game.date,
        "sportsbooks": []
    }

    for odd in odds:
        comparison["sportsbooks"].append({
            "provider": odd.provider_name,
            "spread": odd.spread,
            "over_under": odd.over_under,
            "home_moneyline": odd.home_team_moneyline,
            "away_moneyline": odd.away_team_moneyline,
            "home_spread": odd.home_team_spread,
            "away_spread": odd.away_team_spread,
            "home_spread_odds": odd.home_team_spread_odds,
            "away_spread_odds": odd.away_team_spread_odds
        })

    # Find best lines for bettor
    if comparison["sportsbooks"]:
        best_home_ml = max((s for s in comparison["sportsbooks"] if s["home_moneyline"]),
                           key=lambda x: x["home_moneyline"], default=None)
        best_away_ml = max((s for s in comparison["sportsbooks"] if s["away_moneyline"]),
                           key=lambda x: x["away_moneyline"], default=None)

        comparison["best_lines"] = {
            "home_moneyline": {
                "provider": best_home_ml["provider"] if best_home_ml else None,
                "line": best_home_ml["home_moneyline"] if best_home_ml else None
            },
            "away_moneyline": {
                "provider": best_away_ml["provider"] if best_away_ml else None,
                "line": best_away_ml["away_moneyline"] if best_away_ml else None
            }
        }

    return comparison
