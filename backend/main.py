from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.routes import games, teams, players, analytics, betting, seasons
from core.config import settings
from core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting up NCAA Basketball API")
    # Create tables if they don't exist (for dev)
    # Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down NCAA Basketball API")


app = FastAPI(
    title="NCAA Basketball Analytics API",
    description="High-performance API for NCAA basketball data, analytics, and predictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games.router, prefix="/api/v1/games", tags=["games"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(betting.router, prefix="/api/v1/betting", tags=["betting"])
app.include_router(seasons.router, prefix="/api/v1/seasons", tags=["seasons"])


@app.get("/")
async def root():
    return {
        "message": "NCAA Basketball Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
