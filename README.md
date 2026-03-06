# ElementsRPG -- Backend

Hybrid Active + Idle ElementsRPG backend. Auto-combat survival, monster collection/taming, persistent skill progression, strategy AI customization, life skills economy, convenience-based monetization.

## Tech Stack

- **Runtime**: Python 3.11+
- **Framework**: FastAPI + uvicorn
- **Data Models**: Pydantic v2
- **Database**: Supabase PostgreSQL (SQLAlchemy async + asyncpg)
- **Auth**: Supabase Auth (JWT)
- **Package Manager**: UV
- **Deployment**: Docker + Render

## Quick Start (Local Development)

```bash
# 1. Install dependencies
uv sync

# 2. Copy environment template and fill in values
cp .env.example .env
# Edit .env with your Supabase credentials (see Environment Variables below)

# 3. Run database migrations
uv run alembic upgrade head

# 4. Start the API server
uv run uvicorn elements_rpg.api.app:create_app --factory --reload --port 8000

# 5. Open API docs
# http://localhost:8000/docs
```

## Environment Variables

All variables use the `ELEMENTS_` prefix:

| Variable | Required | Description |
|----------|----------|-------------|
| `ELEMENTS_SUPABASE_URL` | Yes | Supabase project URL (e.g., `https://xxx.supabase.co`) |
| `ELEMENTS_SUPABASE_KEY` | Yes | Supabase anon/public key (client-safe) |
| `ELEMENTS_SUPABASE_SERVICE_KEY` | Yes | Supabase service_role key (backend only, keep secret) |
| `ELEMENTS_SUPABASE_JWT_SECRET` | Yes | JWT secret for token verification |
| `ELEMENTS_DATABASE_URL` | Yes | PostgreSQL connection string (e.g., `postgresql+asyncpg://...`) |
| `ELEMENTS_CORS_ORIGINS` | No | JSON array of allowed origins (default: `["http://localhost:*"]`) |
| `ELEMENTS_DEBUG` | No | Enable debug mode (default: `false`) |
| `ELEMENTS_PORT` | No | Server port (default: `8000`) |

## Development Commands

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest src/elements_rpg/api/tests/test_e2e.py -v

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Auto-fix lint issues
uv run ruff check --fix src/

# Type checking
uv run mypy src/elements_rpg/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
src/elements_rpg/
    api/                 # FastAPI application layer
        app.py           # App factory (CORS, error handlers, routers)
        auth.py          # Supabase JWT verification
        config.py        # pydantic-settings (env vars)
        schemas.py       # Shared API schemas (SuccessResponse, ErrorResponse)
        routers/         # Domain routers (13 routers, 73 endpoints)
        tests/           # API integration + E2E tests
    db/                  # SQLAlchemy models + session management
        models/          # Database models (player, monster, team, economy, etc.)
    services/            # Business logic layer (bridges routers <-> game logic)
    combat/              # Combat system & strategy AI
    monsters/            # Monster models, bestiary, taming
    skills/              # Skill progression system
    economy/             # Areas, crafting, premium, subscriptions
    idle/                # Idle/offline progression
```

Each game logic module follows vertical slice architecture with co-located tests.

## API Documentation

When the server is running, interactive API docs are available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Domains (73 endpoints)

| Domain | Prefix | Endpoints | Auth Required |
|--------|--------|-----------|---------------|
| System | `/health` | 1 | No |
| Auth | `/auth` | 4 | Partial |
| Save/Load | `/saves` | 4 | Yes |
| Monsters | `/monsters` | 7 | Partial |
| Teams | `/teams` | 6 | Yes |
| Combat | `/combat` | 5 | Yes |
| Taming | `/taming` | 3 | Yes |
| Economy | `/economy` | 6 | Partial |
| Crafting | `/crafting` | 5 | Partial |
| Idle/Offline | `/idle` | 8 | Yes |
| Skills | `/skills` | 5 | Partial |
| Premium | `/premium` | 11 | Partial |

## Docker

```bash
# Build the image
docker build -t elements-rpg .

# Run locally with env vars
docker run -p 8000:8000 \
  -e ELEMENTS_SUPABASE_URL=https://xxx.supabase.co \
  -e ELEMENTS_SUPABASE_KEY=your-anon-key \
  -e ELEMENTS_SUPABASE_SERVICE_KEY=your-service-key \
  -e ELEMENTS_SUPABASE_JWT_SECRET=your-jwt-secret \
  -e ELEMENTS_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e ELEMENTS_CORS_ORIGINS='["http://localhost:3000"]' \
  elements-rpg

# Verify
curl http://localhost:8000/health
```

## Deployment to Render

1. **Push to GitHub**: Ensure your code is pushed to the `main` branch.

2. **Create a Render Web Service**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" -> "Web Service"
   - Connect your GitHub repo
   - Render will detect `render.yaml` and auto-configure

3. **Set Environment Variables** in Render dashboard:
   - `ELEMENTS_SUPABASE_URL`
   - `ELEMENTS_SUPABASE_KEY`
   - `ELEMENTS_SUPABASE_SERVICE_KEY`
   - `ELEMENTS_SUPABASE_JWT_SECRET`
   - `ELEMENTS_DATABASE_URL`
   - `ELEMENTS_CORS_ORIGINS` (set to your frontend domain, e.g., `["https://your-app.vercel.app"]`)

4. **Deploy**: Render auto-deploys on push to `main`. The health check at `/health` verifies the service is running.

5. **Verify**: Visit `https://your-service.onrender.com/docs` for API docs.

### Render Configuration (`render.yaml`)

The included `render.yaml` configures:
- Docker runtime with health check at `/health`
- Auto-deploy from `main` branch
- All required environment variables (set via Render dashboard)

## Core Systems

**Combat**: Full auto-combat with damage calculations, critical hits, status effects, 5 AI strategies

**Monsters**: 12 species, leveling, bonding, 4-skill slots, passive traits, taming with pity system

**Economy**: Gold/gems, crafting recipes, material inventory, 2 areas with exclusive resources

**Idle**: Offline progression (85% efficiency, 8hr cap), BRPM tracking, action queue (2+ slots)

**Skills**: 28 unique skills, usage-based leveling, milestone upgrades, strategy proficiency

**Monetization**: Convenience-only gems, subscriptions (monthly/quarterly/annual), reward ads with cooldowns

## Project Status

All 7 phases complete:
- **Phase 1**: Foundation -- Python project, Pydantic models, development setup
- **Phase 2**: Core Systems -- Combat, monsters, skills, strategy AI, taming
- **Phase 3**: Economy & Idle -- Offline progression, life skills, action queue, resources
- **Phase 4**: Team & Areas -- Teams, 2 areas, 12 monsters, 28 skills
- **Phase 5**: Monetization -- Gems, reward ads, subscriptions, save/load
- **Phase 6**: Deployment -- FastAPI, Docker, Render, CI/CD, Supabase integration
- **Phase 7**: Polish -- E2E tests, security hardening, API documentation

## Testing

- 1077+ tests with 99% coverage
- E2E test suite covering full player journey (15 steps)
- API integration tests for all 13 routers
- Unit tests for all game logic modules
- Ruff for linting (line-length=100, double quotes)
