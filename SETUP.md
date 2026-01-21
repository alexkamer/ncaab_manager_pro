# NCAA Basketball Analytics Platform - Setup Guide

This is a high-end, production-grade web application for NCAA basketball analytics, predictions, and betting intelligence.

## Architecture Overview

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Caching**: Redis for performance optimization
- **API**: RESTful with OpenAPI documentation

### Frontend (Next.js 14)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with dark mode
- **State Management**: TanStack Query + Zustand
- **Data Visualization**: Recharts

## Prerequisites

Before starting, ensure you have installed:
- Python 3.12+
- uv (Python package manager)
- Node.js 20+
- Docker & Docker Compose (optional, for containerized setup)

## Setup Methods

### Method 1: Manual Setup with uv (Recommended)

#### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Install dependencies using uv**:
```bash
uv pip install -r requirements.txt
```

Or add them individually:
```bash
uv add fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings python-multipart redis httpx pandas
```

3. **Create environment file**:
```bash
cp .env.example .env
```

4. **Start the backend server**:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

#### Frontend Setup

1. **Navigate to frontend directory** (in a new terminal):
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Create environment file**:
```bash
cp .env.local.example .env.local
```

4. **Start the development server**:
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

#### Optional: Redis Setup

For caching (improves performance):

1. **Install Redis** (macOS):
```bash
brew install redis
```

2. **Start Redis**:
```bash
redis-server
```

3. **Enable Redis in backend**:
Edit `backend/.env`:
```
REDIS_ENABLED=true
```

### Method 2: Docker (Alternative)

1. **Start all services**:
```bash
docker-compose up
```

This will start:
- Backend API on http://localhost:8000
- Frontend on http://localhost:3000
- Redis on localhost:6379

2. **View API documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. **Stop services**:
```bash
docker-compose down
```

## Testing the Application

### 1. Test Backend API

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Get Today's Games
```bash
curl http://localhost:8000/api/v1/games/today
```

#### Get All Teams
```bash
curl http://localhost:8000/api/v1/teams?limit=10
```

#### Get Power Rankings
```bash
curl "http://localhost:8000/api/v1/analytics/power-rankings?season=2026&limit=25"
```

#### Get Betting Edges
```bash
curl "http://localhost:8000/api/v1/analytics/betting-edges?min_edge=5.0"
```

#### Search Teams
```bash
curl "http://localhost:8000/api/v1/teams?search=Duke"
```

#### Get Team Schedule
```bash
# First get a team ID from the teams endpoint, then:
curl "http://localhost:8000/api/v1/teams/{TEAM_ID}/schedule?season=2026"
```

#### Get Game Details
```bash
# First get a game ID from games endpoint, then:
curl http://localhost:8000/api/v1/games/{GAME_ID}
```

#### Get Game Boxscore
```bash
curl http://localhost:8000/api/v1/games/{GAME_ID}/boxscore
```

### 2. Test Frontend

Open your browser and test these pages:

1. **Homepage** - http://localhost:3000
   - Should display today's games
   - Check game cards with scores/times
   - Verify team logos load

2. **Teams Page** - http://localhost:3000/teams
   - Search for teams (try "Duke", "Kansas", etc.)
   - Click on a team card

3. **Players Page** - http://localhost:3000/players
   - Search for players
   - Verify player information displays

4. **Analytics Page** - http://localhost:3000/analytics
   - Check power rankings table
   - Try different seasons

5. **Betting Page** - http://localhost:3000/betting
   - View betting edges
   - Check prediction vs Vegas comparison

### 3. Test API Documentation

Visit http://localhost:8000/docs to:
- Browse all API endpoints
- Test endpoints directly in the browser
- View request/response schemas

## Common Testing Scenarios

### Scenario 1: Browse Today's Games
1. Go to homepage
2. Verify games load with correct scores/times
3. Click on a game card
4. Should navigate to game detail page

### Scenario 2: Search for a Team
1. Go to Teams page
2. Search for "Duke" or "North Carolina"
3. Click on team
4. View team schedule and stats

### Scenario 3: Check Power Rankings
1. Go to Analytics page
2. Select season (2026, 2025, etc.)
3. Verify rankings load with win percentages
4. Check team colors display correctly

### Scenario 4: Find Betting Value
1. Go to Betting page
2. View betting edges
3. Check prediction vs Vegas implied probability
4. Verify recommended bets display

## Performance Testing

### Backend Performance
```bash
# Test API response time
time curl http://localhost:8000/api/v1/games/today

# Load test (requires Apache Bench)
ab -n 1000 -c 10 http://localhost:8000/api/v1/games/today
```

### Frontend Performance
1. Open Chrome DevTools
2. Go to Network tab
3. Check page load time
4. Verify images lazy load

## Troubleshooting

### Backend Issues

**Port 8000 already in use**:
```bash
lsof -ti:8000 | xargs kill -9
```

**Database locked**:
- Close any other processes accessing the database
- Restart the backend server

**Module not found**:
```bash
uv pip install -r requirements.txt --force-reinstall
```

Or reinstall individually:
```bash
uv add fastapi uvicorn sqlalchemy pydantic
```

### Frontend Issues

**Port 3000 already in use**:
```bash
lsof -ti:3000 | xargs kill -9
```

**Dependencies issue**:
```bash
rm -rf node_modules package-lock.json
npm install
```

**Build errors**:
```bash
rm -rf .next
npm run dev
```

### Redis Issues

**Connection refused**:
- Check if Redis is running: `redis-cli ping`
- If not, disable in `.env`: `REDIS_ENABLED=false`

## Production Deployment

### Backend with uv
```bash
cd backend
uv pip install -r requirements.txt
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

### Environment Variables

**Backend** (.env):
```
DATABASE_URL=sqlite:///data/ncaab.db
REDIS_ENABLED=true
REDIS_HOST=localhost
CORS_ORIGINS=["https://yourdomain.com"]
```

**Frontend** (.env.local):
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Features Available

### Current Features
- ✅ Games browsing with filters
- ✅ Team directory and profiles
- ✅ Player search and profiles
- ✅ Power rankings
- ✅ Betting edges analysis
- ✅ Game boxscores
- ✅ Team schedules and stats
- ✅ Player game logs
- ✅ Conference standings
- ✅ Odds comparison

### API Endpoints
- `/api/v1/games` - Games with filtering
- `/api/v1/teams` - Teams directory
- `/api/v1/players` - Players search
- `/api/v1/analytics` - Advanced analytics
- `/api/v1/betting` - Betting intelligence

## Next Steps

1. **Add Authentication**: Implement user accounts for premium features
2. **Real-time Updates**: Add WebSocket for live game updates
3. **Advanced Analytics**: More sophisticated prediction models
4. **Mobile Apps**: React Native for iOS/Android
5. **Payment Integration**: Stripe for premium subscriptions
6. **Email Notifications**: Game alerts and betting edges
7. **Social Features**: User comments and predictions

## Support

For issues or questions:
- Check API docs: http://localhost:8000/docs
- Review error logs in terminal
- Verify database has data (60K+ games)

## Database Stats

Your database contains:
- 60,032 games (2002-2026)
- 362 teams
- 17,749 players
- Odds from multiple sportsbooks
- ESPN predictions
- Complete boxscores
