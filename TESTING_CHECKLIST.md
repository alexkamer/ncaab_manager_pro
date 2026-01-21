# Testing Checklist

## Quick Start Test (5 minutes)

### Manual Setup with uv (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
uv pip install -r requirements.txt
uv run uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Wait for services to start, then test:
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Option 2: Docker

```bash
# From project root
docker-compose up
```

## What to Test

### 1. Backend API Tests (http://localhost:8000)

```bash
# Health check
curl http://localhost:8000/health

# Today's games
curl http://localhost:8000/api/v1/games/today

# Get all teams
curl http://localhost:8000/api/v1/teams?limit=10

# Search teams
curl "http://localhost:8000/api/v1/teams?search=Duke"

# Power rankings
curl "http://localhost:8000/api/v1/analytics/power-rankings?season=2026&limit=10"

# Betting edges
curl "http://localhost:8000/api/v1/analytics/betting-edges?min_edge=5"

# Get games with filters
curl "http://localhost:8000/api/v1/games?season=2026&limit=5"
```

### 2. Frontend Tests (http://localhost:3000)

**Homepage:**
- [ ] Today's games load
- [ ] Game cards show correctly
- [ ] Scores display for completed games
- [ ] Team logos load

**Teams Page:**
- [ ] Search works (try "Duke", "Kansas")
- [ ] Team cards display
- [ ] Team colors show correctly

**Players Page:**
- [ ] Search functionality works
- [ ] Player information displays
- [ ] Height/weight/jersey show

**Analytics Page:**
- [ ] Power rankings table loads
- [ ] Season selector works
- [ ] Win percentages calculate correctly

**Betting Page:**
- [ ] Betting edges load
- [ ] Prediction vs Vegas shows
- [ ] Recommended bets display

### 3. Interactive API Testing

Visit http://localhost:8000/docs and test:
- [ ] GET /api/v1/games/today
- [ ] GET /api/v1/teams
- [ ] GET /api/v1/analytics/power-rankings
- [ ] GET /api/v1/betting/lines

## Expected Results

### API Should Return:
- Games: Array of game objects with scores, teams, dates
- Teams: 362 teams total
- Players: 17,749+ players
- Power Rankings: Top 25 teams by win percentage
- Betting Edges: Games where model disagrees with Vegas

### Frontend Should Display:
- Dark mode theme
- Smooth animations
- Responsive layout
- Team colors
- Live game indicators
- Glass morphism effects

## Common Issues & Solutions

**Backend won't start:**
```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Reinstall dependencies with uv
cd backend
uv pip install -r requirements.txt
```

**Frontend won't start:**
```bash
# Clear and reinstall
rm -rf node_modules .next
npm install
```

**No data showing:**
- Check that `data/ncaab.db` exists (867MB file)
- Verify database has 60K+ games
- Check API is accessible from frontend

**CORS errors:**
- Backend should allow localhost:3000
- Check CORS_ORIGINS in backend/.env

## Performance Benchmarks

Expected performance:
- API response time: < 200ms
- Page load time: < 2s
- Games query: < 100ms
- Power rankings: < 500ms

## What Works

✅ **Backend API**
- Games endpoint with filtering
- Teams directory and profiles
- Player search and stats
- Power rankings algorithm
- Betting edge detection
- Conference standings
- Game boxscores
- Odds comparison

✅ **Frontend**
- Homepage with today's games
- Teams directory with search
- Players directory with search
- Analytics dashboard
- Betting intelligence page
- Responsive design
- Dark mode
- Smooth animations

## Next Features to Build

🚧 **Phase 2** (Next steps):
1. Individual game detail pages
2. Individual team profile pages
3. Individual player profile pages
4. Data visualizations (charts/graphs)
5. Conference standings page
6. Historical matchup analysis
7. Live game updates
8. User authentication

## Quick Test Script

```bash
#!/bin/bash

echo "Testing Backend API..."
curl -s http://localhost:8000/health && echo "✅ Backend health check passed"
curl -s http://localhost:8000/api/v1/games/today | grep -q "id" && echo "✅ Games endpoint working"
curl -s http://localhost:8000/api/v1/teams?limit=1 | grep -q "id" && echo "✅ Teams endpoint working"

echo "\nVisit http://localhost:3000 to test frontend"
echo "Visit http://localhost:8000/docs for API documentation"
```

Save as `test.sh`, make executable with `chmod +x test.sh`, then run `./test.sh`
