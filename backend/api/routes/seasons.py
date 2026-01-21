from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from core.database import get_db
from models.models import Season

router = APIRouter()


@router.get("/current")
def get_current_season(db: Session = Depends(get_db)):
    """Get the most recent season"""
    season = db.query(Season).order_by(desc(Season.year)).first()

    if not season:
        raise HTTPException(status_code=404, detail="No seasons found")

    return {
        "year": season.year,
        "displayName": season.displayName,
        "startDate": season.startDate,
        "endDate": season.endDate
    }


@router.get("/")
def get_all_seasons(db: Session = Depends(get_db)):
    """Get all seasons"""
    seasons = db.query(Season).order_by(desc(Season.year)).all()

    return [
        {
            "year": season.year,
            "displayName": season.displayName,
            "startDate": season.startDate,
            "endDate": season.endDate
        }
        for season in seasons
    ]


@router.get("/{year}")
def get_season(year: int, db: Session = Depends(get_db)):
    """Get a specific season by year"""
    season = db.query(Season).filter(Season.year == year).first()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    return {
        "year": season.year,
        "displayName": season.displayName,
        "startDate": season.startDate,
        "endDate": season.endDate
    }
