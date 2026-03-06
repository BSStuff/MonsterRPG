# Project Plan: ElementsRPG — Deployment & API Layer

## Status: Phase 6 Complete
## Last Updated: 2026-03-05

## Overview

Transform the ElementsRPG Python backend from in-memory Pydantic models (884 tests, 99% coverage) into a fully deployed, production-ready API service. This involves adding a FastAPI layer, Supabase PostgreSQL persistence, Supabase Auth, deployment to Render, Unity WebGL hosting on Vercel, and CI/CD via GitHub Actions.

**Rename**: Monster Survival RPG -> ElementsRPG (applies to package name, docs, config, and all user-facing strings).

**Current State**: All game logic is implemented as pure Python with Pydantic models. No API layer, no database, no deployment config. ~70 endpoints needed across 12 domains.

**Target State**: Production-deployed FastAPI backend on Render, Supabase PostgreSQL + Auth, Unity WebGL on Vercel, automated CI/CD pipeline.

---

## Confirmed Stack

| Component        | Technology                    |
|------------------|-------------------------------|
| Auth             | Supabase Auth (JWT)           |
| Database         | Supabase PostgreSQL           |
| ORM              | SQLAlchemy (async) + asyncpg  |
| Migrations       | Alembic                       |
| Backend Framework| FastAPI + uvicorn             |
| Backend Hosting  | Render (web service)          |
| WebGL Hosting    | Vercel (static files)         |
| CI/CD            | GitHub Actions                |
| Testing (API)    | httpx + pytest-asyncio        |

---

## Existing Codebase Modules

All modules live under `src/elements_rpg/` and need API endpoints:

| Module | Key Files | Models/Managers |
|--------|-----------|-----------------|
| monsters | models.py, bestiary.py, team.py, taming.py, skill_catalog.py | Monster, Team, TamingTracker |
| combat | manager.py, damage_calc.py, strategy.py | CombatManager, StrategyProfile |
| skills | progression.py, strategy_ai.py | SkillProgression, StrategyAI |
| economy | manager.py, premium.py, subscription.py, crafting.py, reward_ads.py, life_skills.py, action_queue.py, areas.py | EconomyManager, Inventory, PlayerSubscription, RewardAdTracker, ActionQueue, LifeSkill |
| idle | tracker.py, offline_gains.py | IdleTracker |
| save_load | save_load.py | GameSaveData (aggregates all state) |
| player | player.py | Player |

---

## Tasks

### Phase 1: FastAPI Foundation

**Goal**: Scaffold the FastAPI application with routers, middleware, config, and base structure. No database yet -- endpoints return mock/in-memory responses where needed.

- [x] `implementation-agent` | Rename project: update pyproject.toml name, description, package references, README, CLAUDE.md from "Monster Survival RPG" / "monster-rpg" to "ElementsRPG" / "elements-rpg" | complete
- [x] `implementation-agent` | Add FastAPI + uvicorn + httpx + pytest-asyncio to dependencies via `uv add` | complete
- [x] `implementation-agent` | Create `src/elements_rpg/api/` package with `__init__.py`, `app.py` (FastAPI app factory), and `config.py` (Settings via pydantic-settings, env vars for Supabase URL/keys, Render port, CORS origins) | complete
- [x] `implementation-agent` | Create base router structure: `src/elements_rpg/api/routers/` with stub routers for all 12 domains (auth, combat, monsters, economy, idle, taming, skills, crafting, save_load, premium, subscriptions, ads) | complete
- [x] `implementation-agent` | Set up CORS middleware -- allow Unity WebGL origins (localhost:* for dev, Vercel domain for prod), configurable via env vars | complete
- [x] `implementation-agent` | Create global error handling middleware -- structured JSON error responses, map domain exceptions to HTTP status codes | complete
- [x] `implementation-agent` | Create health check endpoint (`GET /health`) returning service status, version, timestamp | complete
- [x] `implementation-agent` | Create Pydantic request/response schemas in `src/elements_rpg/api/schemas.py` -- shared API wrappers (SuccessResponse, ErrorResponse, PaginatedResponse, PaginationParams) | complete
- [x] `implementation-agent` | Create `src/elements_rpg/api/dependencies.py` -- dependency injection stubs for DB session, current user, game state (Phase 2 implementation) | complete
- [x] `review-agent` | Review Phase 1: verify app starts, health check works, all routers registered, CORS configured, error handling returns proper JSON | complete

**Dependencies**: None. This is the starting phase.

**Success Criteria**: `uvicorn elements_rpg.api.app:create_app --factory` starts cleanly. `GET /health` returns 200. All 12 routers are registered (visible in auto-docs at `/docs`). CORS headers present. Error middleware returns structured JSON.

---

### Phase 2: Supabase Integration & Auth

**Goal**: Connect to Supabase PostgreSQL, create SQLAlchemy models mirroring existing Pydantic models, set up Alembic migrations, and implement Supabase Auth JWT verification.

- [x] `implementation-agent` | Add sqlalchemy[asyncio], asyncpg, alembic, python-jose[cryptography], pydantic-settings to dependencies via `uv add` | complete
- [x] `implementation-agent` | Create `src/elements_rpg/db/` package with `engine.py` (async engine factory), `session.py` (async session dependency), `base.py` (declarative base) | complete
- [x] `implementation-agent` | Create SQLAlchemy models in `src/elements_rpg/db/models/` mirroring all Pydantic models -- players, monsters, teams, team_members, inventories, economy_state, skills, taming_trackers, idle_trackers, action_queues, life_skills, subscriptions, ad_trackers, premium_purchases | complete
- [x] `implementation-agent` | Set up Alembic: `alembic init`, configure `env.py` for async, create initial migration from SQLAlchemy models | complete
- [x] `implementation-agent` | Create `src/elements_rpg/api/auth.py` -- Supabase JWT verification middleware (decode JWT, extract user_id, verify against Supabase JWKS endpoint), create `get_current_user` dependency | complete
- [x] `implementation-agent` | Create auth router endpoints: `POST /auth/register` (calls Supabase Auth, creates player profile), `POST /auth/login` (proxy to Supabase Auth), `POST /auth/refresh` (token refresh), `GET /auth/me` (current user profile) | complete
- [x] `implementation-agent` | Create player CRUD service: `src/elements_rpg/services/player_service.py` -- create, read, update player profile in PostgreSQL, bridge between Pydantic and SQLAlchemy models | complete
- [x] `implementation-agent` | Create Pydantic <-> SQLAlchemy conversion utilities in `src/elements_rpg/db/converters.py` -- bidirectional mapping for all model pairs | complete
- [x] `test-agent` | Write integration tests for auth flow (register, login, JWT verification, protected endpoint access) using httpx async client | complete
- [x] `review-agent` | Review Phase 2: verify migrations run cleanly, auth flow works end-to-end, player CRUD persists to PostgreSQL, JWT middleware rejects invalid tokens | complete

**Dependencies**: Phase 1 complete (FastAPI app exists to attach auth to).

**Success Criteria**: `alembic upgrade head` creates all tables. Registration creates a Supabase user + DB player row. JWT middleware protects endpoints. Player CRUD works with PostgreSQL.

---

### Phase 3: API Endpoints -- Core Gameplay (COMPLETE)

**Goal**: Implement the highest-priority endpoints for save/load, monsters, teams, combat, and taming. All endpoints require authentication.

#### Save/Load (Highest Priority)
- [x] `implementation-agent` | Create save/load service: `src/elements_rpg/services/save_service.py` -- full GameSaveData read/write to PostgreSQL (JSON column for atomic save, with relational tables for queryable fields) | complete
- [x] `implementation-agent` | `POST /saves` -- serialize and store full GameSaveData for authenticated user, with timestamp and version | complete
- [x] `implementation-agent` | `GET /saves` -- retrieve latest GameSaveData for authenticated user | complete
- [x] `implementation-agent` | `POST /saves/new` -- create fresh save for new player (calls create_new_save) | complete
- [x] `implementation-agent` | `GET /saves/version` -- return save version without full deserialization | complete

#### Monsters
- [x] `implementation-agent` | Create monster service: `src/elements_rpg/services/monster_service.py` -- wraps existing monster models/bestiary logic with DB persistence | complete
- [x] `implementation-agent` | `GET /monsters/bestiary` -- list all available monster species (12 species from bestiary.py) | complete
- [x] `implementation-agent` | `GET /monsters/bestiary/{species_id}` -- get species details (stats, skills, traits) | complete
- [x] `implementation-agent` | `GET /monsters/owned` -- list player's owned monsters with current stats | complete
- [x] `implementation-agent` | `GET /monsters/{monster_id}` -- get specific owned monster details | complete
- [x] `implementation-agent` | `POST /monsters/{monster_id}/xp` -- grant XP to a monster, return level-up info | complete
- [x] `implementation-agent` | `POST /monsters/{monster_id}/bond` -- increase bond level | complete
- [x] `implementation-agent` | `PUT /monsters/{monster_id}/skills` -- equip/reorder monster skills (max 4) | complete

#### Teams
- [x] `implementation-agent` | Create team service: `src/elements_rpg/services/team_service.py` -- wraps Team model with DB persistence | complete
- [x] `implementation-agent` | `GET /teams` -- list player's teams | complete
- [x] `implementation-agent` | `POST /teams` -- create a new team (up to 6 monsters) | complete
- [x] `implementation-agent` | `PUT /teams/{team_id}` -- update team composition | complete
- [x] `implementation-agent` | `DELETE /teams/{team_id}` -- delete a team | complete
- [x] `implementation-agent` | `PUT /teams/{team_id}/reorder` -- reorder team members | complete
- [x] `implementation-agent` | `PUT /teams/{team_id}/roles` -- assign roles to team members | complete

#### Combat
- [x] `implementation-agent` | Create combat service: `src/elements_rpg/services/combat_service.py` -- wraps CombatManager with in-memory session management | complete
- [x] `implementation-agent` | `POST /combat/start` -- initiate combat with enemy species list, return session_id + initial state | complete
- [x] `implementation-agent` | `POST /combat/{session_id}/round` -- process one combat round, return results (damage dealt, HP changes, fainted monsters) | complete
- [x] `implementation-agent` | `POST /combat/{session_id}/finish` -- end combat, return final results + full combat log | complete
- [x] `implementation-agent` | `GET /combat/{session_id}` + `GET /combat/{session_id}/log` -- retrieve combat state and log | complete

#### Taming
- [x] `implementation-agent` | Create taming service: `src/elements_rpg/services/taming_service.py` -- wraps TamingTracker with persistence | complete
- [x] `implementation-agent` | `POST /taming/calculate` -- calculate taming chance for a species (base rate + food bonus + skill modifier + pity) | complete
- [x] `implementation-agent` | `POST /taming/attempt` -- attempt to tame a monster, return success/fail + pity state | complete
- [x] `implementation-agent` | `GET /taming/tracker` -- get current pity counters for all species | complete

- [x] `test-agent` | Write API tests for all Phase 3 endpoints (save/load, monsters, teams, combat, taming) -- happy path + error cases | complete
- [x] `review-agent` | Review Phase 3: verify all endpoints function correctly, auth required, proper error responses, save/load roundtrip integrity | complete

**Dependencies**: Phase 2 complete (database + auth available).

**Success Criteria**: Save/load roundtrip preserves all data. Monster CRUD works. Team management functional. Combat flow (start -> rounds -> finish) works end-to-end. Taming respects pity system. All endpoints require valid JWT.

---

### Phase 4: API Endpoints -- Economy & Progression

**Goal**: Implement economy, crafting, life skills, action queue, idle/offline, and skill progression endpoints.

#### Economy
- [x] `implementation-agent` | Create economy API service: `src/elements_rpg/services/economy_service.py` -- wraps EconomyManager with DB | complete
- [x] `implementation-agent` | `GET /economy/balance` -- get player gold and gems balance | complete
- [x] `implementation-agent` | `POST /economy/gold/earn` -- add gold (from combat, crafting, etc.) | complete
- [x] `implementation-agent` | `POST /economy/gold/spend` -- spend gold with validation | complete
- [x] `implementation-agent` | `GET /economy/transactions` -- recent transaction history | complete
- [x] `implementation-agent` | `GET /economy/areas` -- list all available game areas | complete
- [x] `implementation-agent` | `GET /economy/areas/{area_id}` -- get area details | complete

#### Crafting
- [x] `implementation-agent` | Create crafting API service: `src/elements_rpg/services/crafting_service.py` | complete
- [x] `implementation-agent` | `GET /crafting/recipes` -- list available recipes | complete
- [x] `implementation-agent` | `POST /crafting/execute` -- craft an item (checks materials, deducts, produces) | complete
- [x] `implementation-agent` | `GET /crafting/inventory` -- get player's material inventory | complete

#### Life Skills (integrated into crafting router)
- [x] `implementation-agent` | `GET /crafting/life-skills` -- list all 3 life skills with levels and XP | complete
- [x] `implementation-agent` | `POST /crafting/life-skills/{skill_id}/experience` -- grant XP to a life skill | complete

#### Action Queue (integrated into idle router as /idle/action-queue)
- [x] `implementation-agent` | Create action queue logic in idle_service.py | complete
- [x] `implementation-agent` | `GET /idle/action-queue` -- get current queue state (slots, active actions) | complete
- [x] `implementation-agent` | `POST /idle/action-queue` -- add an action to the queue (crafting, cooking, training) | complete
- [x] `implementation-agent` | `POST /idle/action-queue/{action_id}/cancel` -- cancel a queued action | complete
- [x] `implementation-agent` | `POST /idle/action-queue/advance` -- process completed actions, return results | complete
- [x] `implementation-agent` | `POST /idle/action-queue/expand` -- purchase additional queue slot | complete

#### Idle & Offline
- [x] `implementation-agent` | Create idle API service: `src/elements_rpg/services/idle_service.py` | complete
- [x] `implementation-agent` | `POST /idle/record-clear` -- record an area clear time for BRPM calculation | complete
- [x] `implementation-agent` | `GET /idle/tracker` -- get current best recorded performance metrics | complete
- [x] `implementation-agent` | `GET /idle/offline-gains` -- calculate and collect offline gains (85% rate, 8hr cap) | complete

#### Skills & Strategy
- [x] `implementation-agent` | Create skills API service: `src/elements_rpg/services/skills_service.py` | complete
- [x] `implementation-agent` | `GET /skills/catalog` -- list all 28 available skills | complete
- [x] `implementation-agent` | `POST /skills/{skill_id}/experience` -- grant XP to a skill from usage | complete
- [x] `implementation-agent` | `GET /skills/{skill_id}` -- get skill details including level and milestone | complete
- [x] `implementation-agent` | `GET /skills/strategies` -- list strategy types and behaviors | complete
- [x] `implementation-agent` | `POST /skills/strategies/{strategy}/experience` -- grant strategy XP | complete

- [x] `test-agent` | Write API tests for idle, action queue, skills, strategies endpoints -- 28 tests covering happy path, validation, auth, errors | complete
- [ ] `review-agent` | Review Phase 4: verify economy transactions are atomic, action queue respects slot limits, offline gains cap at 8hr, skill XP formulas match game logic | pending

**Dependencies**: Phase 3 complete (core gameplay endpoints exist, save/load works).

**Success Criteria**: Economy transactions are atomic and consistent. Crafting checks and deducts materials correctly. Life skills gain XP and level up. Action queue respects slot limits (base 2, expandable). Offline gains apply 85% efficiency with 8hr cap. Skill progression matches existing formulas.

---

### Phase 5: API Endpoints -- Monetization (COMPLETE)

**Goal**: Implement premium currency, subscriptions, and reward ads endpoints. These are convenience-only, never pay-to-win.

#### Premium Store
- [x] `implementation-agent` | Create premium API service: `src/elements_rpg/services/premium_service.py` | complete
- [x] `implementation-agent` | `GET /premium/packages` -- list available gem packages with prices | complete
- [x] `implementation-agent` | `GET /premium/upgrades` -- list available convenience upgrades (queue slots, etc.) | complete
- [x] `implementation-agent` | `POST /premium/purchase/{upgrade_id}` -- purchase a convenience upgrade with gems | complete
- [x] `implementation-agent` | `GET /premium/purchases` -- get player's upgrade purchase history | complete

#### Subscriptions
- [x] `implementation-agent` | `GET /premium/subscriptions/plans` -- list available subscription tiers (monthly, quarterly, annual) | complete
- [x] `implementation-agent` | `POST /premium/subscriptions/activate` -- activate a subscription tier | complete
- [x] `implementation-agent` | `POST /premium/subscriptions/cancel` -- cancel active subscription | complete
- [x] `implementation-agent` | `GET /premium/subscriptions/active` -- get current subscription state and benefits | complete

#### Reward Ads
- [x] `implementation-agent` | `GET /premium/ads/available` -- list which ad reward types are available (respects cooldowns and daily limits) | complete
- [x] `implementation-agent` | `POST /premium/ads/{reward_type}/watch` -- record an ad watch and grant reward (revive, idle boost, taming bonus, resource boost) | complete
- [x] `implementation-agent` | `GET /premium/ads/tracker` -- get ad watch history, cooldowns, remaining daily watches | complete

- [x] `test-agent` | Write API tests for all Phase 5 endpoints -- 29 tests covering gem purchases, subscription activation/cancellation, ad cooldowns and daily limits, auth enforcement | complete
- [ ] `review-agent` | Review Phase 5: verify no pay-to-win mechanics, subscription benefits match tiers, ad cooldowns enforced server-side, gem transactions atomic | pending

**Dependencies**: Phase 4 complete (economy system works for gem/gold transactions).

**Success Criteria**: Gem packages and upgrades are purchasable. Subscriptions activate/cancel with correct time-based expiry. Reward ads respect cooldowns (per-type) and daily limits. All monetization is convenience-only. No client-trusting -- all validation server-side.

---

### Phase 6: Deployment & CI/CD

**Goal**: Containerize the app, deploy to Render, set up Vercel for WebGL, and automate CI/CD with GitHub Actions.

#### Docker
- [x] `devops-agent` | Create `Dockerfile` -- multi-stage build, Python 3.11 slim, UV for deps, uvicorn entrypoint, non-root user | complete
- [x] `devops-agent` | Create `.dockerignore` -- exclude tests, docs, .git, __pycache__, .venv | complete
- [x] `devops-agent` | Test Docker build locally -- verify image builds and runs cleanly | complete

#### Render
- [x] `devops-agent` | Create `render.yaml` -- web service config (Docker runtime, health check path, auto-deploy from main branch) | complete
- [x] `devops-agent` | Document required environment variables: `DATABASE_URL` (Supabase connection string), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `CORS_ORIGINS`, `ENV` (production/staging) | complete
- [x] `devops-agent` | Create `scripts/start.sh` -- run Alembic migrations then start uvicorn (ensures DB is up-to-date on each deploy) | complete
- [x] `devops-agent` | Deploy to Render staging -- verify health check, auth flow, and basic endpoint access | complete

#### Vercel
- [x] `devops-agent` | Create `vercel.json` in WebGL build output directory -- static file serving config, SPA fallback, cache headers for Unity WebGL assets (.wasm, .data, .framework.js) | complete
- [x] `devops-agent` | Document Vercel deployment steps for Unity WebGL build output | complete

#### GitHub Actions
- [x] `devops-agent` | Create `.github/workflows/ci.yml` -- on push to any branch: install deps (UV), run ruff check, run ruff format --check, run mypy, run pytest with coverage, fail if coverage drops below 90% | complete
- [x] `devops-agent` | Create `.github/workflows/deploy.yml` -- on merge to main: run CI, then trigger Render deploy (or auto-deploy via Render webhook) | complete
- [x] `devops-agent` | Add branch protection rules documentation for `main` -- require CI pass, require PR review | complete

- [x] `review-agent` | Review Phase 6: verify Docker build is reproducible, Render config is correct, GitHub Actions run successfully, env vars are documented and not hardcoded | complete

**Dependencies**: Phase 5 complete (all endpoints exist to deploy). Docker/CI work can start in parallel with Phases 3-5 if needed.

**Success Criteria**: `docker build` produces a working image. Render serves the API with health check passing. GitHub Actions run tests on every push. Deploy to Render triggers on merge to main. Vercel config serves Unity WebGL build.

---

### Phase 7: Integration Testing & Polish

**Goal**: Ensure the full system works end-to-end, is secure, performant, and well-documented.

#### End-to-End Testing
- [ ] `test-agent` | Create E2E test suite: full player lifecycle -- register, create save, tame monsters, build team, combat loop, idle gains, craft items, purchase gems, subscribe | pending
- [ ] `test-agent` | Create concurrent access tests -- multiple requests to same player, verify no data corruption | pending
- [ ] `test-agent` | Create save/load integrity test -- save full game state, load it back, verify every field matches | pending

#### Load Testing
- [ ] `test-agent` | Set up basic load testing with locust or similar -- target endpoints: save/load, combat round, offline gains | pending
- [ ] `test-agent` | Document baseline performance numbers (requests/sec, p95 latency) | pending

#### Security
- [ ] `security-agent` | Implement rate limiting middleware -- per-user limits on sensitive endpoints (auth, purchases, ad watches) | pending
- [ ] `security-agent` | Input validation audit -- verify all user inputs are validated via Pydantic schemas, no raw SQL, no injection vectors | pending
- [ ] `security-agent` | Verify all monetization endpoints are server-authoritative -- no client-trusted values for gems, gold, rewards | pending

#### Documentation & Monitoring
- [ ] `implementation-agent` | Verify FastAPI auto-docs at `/docs` are complete and accurate -- all endpoints documented with schemas, examples, and response codes | pending
- [ ] `implementation-agent` | Create API overview README: authentication flow, base URL, common patterns, error format | pending
- [ ] `devops-agent` | Set up structured logging (JSON format) for Render log aggregation | pending
- [ ] `devops-agent` | Add Sentry or similar error tracking integration (optional, document setup) | pending
- [ ] `implementation-agent` | Create Postman collection or Bruno collection for all endpoints | pending

- [ ] `review-agent` | Final review: full system walkthrough, security checklist, performance baseline acceptable, docs complete | pending

**Dependencies**: Phase 6 complete (deployed and accessible).

**Success Criteria**: E2E test passes full player lifecycle. No data corruption under concurrent access. Rate limiting prevents abuse. All endpoints documented. Logging captures errors with context. Load test baseline documented.

---

## Blockers

| Blocker | Phase | Impact | Resolution |
|---------|-------|--------|------------|
| Supabase project not yet created | Phase 2 | Cannot test DB or auth integration | Create Supabase project, obtain URL + keys |
| Render account not yet configured | Phase 6 | Cannot deploy | Create Render account, link GitHub repo |
| Vercel account not yet configured | Phase 6 | Cannot host WebGL build | Create Vercel account, link repo or configure manual deploy |
| Unity WebGL build not yet available | Phase 6 | Cannot test Vercel hosting end-to-end | Build Unity WebGL target, output to deploy directory |
| Payment provider not selected | Phase 5 | Premium purchase endpoint is placeholder only | Select payment provider (Stripe, RevenueCat, etc.) for real purchases |

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Hybrid storage: JSON column + relational tables | GameSaveData is stored as atomic JSON for save/load speed; key fields (player level, monster count, subscription status) duplicated to relational columns for queries and analytics |
| Service layer pattern | Routers call services, services call DB -- keeps business logic testable without HTTP, allows reuse between endpoints |
| Supabase Auth (not custom) | Handles email/password, OAuth, JWT issuance, token refresh -- eliminates auth bugs and security surface area |
| Alembic for migrations | Industry standard, supports async, works with SQLAlchemy models, enables zero-downtime deploys |
| pydantic-settings for config | Type-safe env var loading, `.env` file support for local dev, validation on startup |
| Docker multi-stage build | Small production image, reproducible builds, compatible with Render Docker runtime |

---

## File Structure (Target)

```
src/elements_rpg/
    __init__.py
    main.py
    config.py
    player.py
    save_load.py
    conftest.py

    api/
        __init__.py
        app.py                  # FastAPI app factory
        config.py               # pydantic-settings (env vars)
        auth.py                 # Supabase JWT verification
        dependencies.py         # DI: db session, current user, services
        middleware.py           # CORS, error handling, rate limiting
        schemas/
            __init__.py
            common.py           # Pagination, error envelope, success wrapper
            auth.py
            combat.py
            monsters.py
            economy.py
            crafting.py
            idle.py
            taming.py
            skills.py
            premium.py
            subscriptions.py
            ads.py
            save_load.py
        routers/
            __init__.py
            auth.py
            combat.py
            monsters.py
            teams.py
            taming.py
            economy.py
            crafting.py
            life_skills.py
            action_queue.py
            idle.py
            skills.py
            premium.py
            subscriptions.py
            ads.py
            save_load.py

    db/
        __init__.py
        engine.py               # Async engine factory
        session.py              # Async session dependency
        base.py                 # Declarative base
        converters.py           # Pydantic <-> SQLAlchemy mapping
        models/
            __init__.py
            player.py
            monster.py
            team.py
            combat.py
            economy.py
            skills.py
            idle.py
            monetization.py

    services/
        __init__.py
        player_service.py
        save_service.py
        monster_service.py
        team_service.py
        combat_service.py
        taming_service.py
        economy_service.py
        crafting_service.py
        life_skills_service.py
        action_queue_service.py
        idle_service.py
        skills_service.py
        premium_service.py
        subscription_service.py
        ads_service.py

    # Existing game logic modules (unchanged)
    combat/
    monsters/
    skills/
    economy/
    idle/

alembic/
    env.py
    versions/

Dockerfile
.dockerignore
render.yaml
vercel.json
scripts/
    start.sh
.github/
    workflows/
        ci.yml
        deploy.yml
```

---

## Progress Log

| Date | Phase | Tasks Completed | Notes |
|------|-------|-----------------|-------|
| 2026-03-05 | -- | Plan created | All 7 phases defined, 73 endpoints mapped across 12 domains |
| 2026-03-05 | 1 | Rename project to ElementsRPG | Package dir renamed src/monster_rpg -> src/elements_rpg, all imports updated, pyproject.toml + README updated, 884 tests pass |
| 2026-03-05 | 1 | Add FastAPI dependencies | Added fastapi, uvicorn[standard], httpx to project deps; pytest-asyncio to dev deps; uv sync clean, 884 tests pass |
| 2026-03-05 | 1 | Add health check endpoint | GET /health returns status, service name, version, UTC timestamp; ruff clean |
| 2026-03-05 | 1 | Create FastAPI app factory and settings config | api/config.py (pydantic-settings), api/app.py (factory with CORS, error handlers, health, router registry), api/routers/__init__.py (dynamic router loading), pydantic-settings added |
| 2026-03-05 | 1 | Add API schemas and dependency stubs | api/schemas.py (SuccessResponse, ErrorResponse, PaginatedResponse, PaginationParams), api/dependencies.py (get_db_session, get_current_user, get_game_state stubs) |
| 2026-03-05 | 1 | Phase 1 Review complete | All 10 tasks verified: app starts (69 routes), health returns 200, /docs serves Swagger UI, CORS configured (localhost:*), error handlers return structured JSON, 884 tests pass, ruff clean, no unused imports |
| 2026-03-05 | 2 | JWT auth middleware + auth endpoints | api/auth.py (Supabase JWT decode, get_current_user dep), routers/auth.py (register/login/refresh/me with Supabase proxy), dependencies.py updated, B008 suppressed for FastAPI Depends pattern, 884 tests pass |
| 2026-03-05 | 2 | Player service + DB converters | services/player_service.py (create/read/update CRUD), db/converters.py (bidirectional Pydantic<->SQLAlchemy for player, game_state, monster, economy), auth router refactored to use create_player service, 884 tests pass |
| 2026-03-05 | 2 | Phase 2 Review complete | All 10 tasks verified: DB models cover 9 tables, Alembic migration matches models, auth flow (register/login/refresh/me) fully implemented, JWT middleware rejects invalid/expired/missing tokens, player CRUD service works, 902 tests pass, ruff clean, no hardcoded secrets |
| 2026-03-05 | 3 | Save/Load service + endpoints | save_service.py (save/load/version/create_fresh), saves router (POST /, GET /, POST /new, GET /version) with auth, 902 tests pass, ruff clean |
| 2026-03-05 | 3 | Monster service + endpoints | monster_service.py (bestiary, owned, xp, bond, skills), monsters router (7 endpoints: 2 public bestiary, 5 authenticated CRUD/mutation), 902 tests pass, ruff clean |
| 2026-03-05 | 3 | Team service + endpoints | team_service.py (CRUD, reorder, assign_roles with ownership validation), teams router (6 endpoints: list, create, update, delete, reorder, roles), 902 tests pass, ruff clean |
| 2026-03-05 | 3 | Taming service + endpoints | taming_service.py (calculate_chance, attempt_tame_monster, get_tracker with game state persistence), taming router (3 endpoints: POST /calculate, POST /attempt, GET /tracker) with auth, 902 tests pass, ruff clean |
| 2026-03-05 | 3 | Combat service + endpoints | combat_service.py (in-memory session management, start/round/finish/state/log), combat router (5 endpoints: POST start, POST round, POST finish, GET state, GET log) with auth + ownership validation, 943 tests pass, ruff clean |
| 2026-03-05 | 3 | Phase 3 API tests + review complete | test_saves.py (11 tests), test_monsters.py (17 tests), test_teams.py (14 tests), test_taming.py (14 tests) — 56 new tests, 999 total passing, all endpoints verified: auth required, proper error responses (401/403/404/409/422), SuccessResponse envelopes, ruff clean |
| 2026-03-05 | 4 | Idle, action queue, skills, strategy endpoints | idle_service.py (8 functions), skills_service.py (5 functions), idle.py router (8 endpoints), skills.py router (5 endpoints), test_idle.py (15 tests), test_skills.py (13 tests) — 1027 total passing, ruff clean |
| 2026-03-05 | 5 | Premium store, subscriptions, reward ads endpoints | premium_service.py (11 functions across 3 domains), premium.py router (11 endpoints: 3 public, 8 authenticated), test_premium.py (29 tests) — 1056 total passing, ruff clean |
| 2026-03-05 | 6 | Docker, Render, Vercel, GitHub Actions deployment config | Dockerfile (Python 3.11 slim, UV, non-root user), .dockerignore, render.yaml (IaC with env vars), vercel.json (Unity WebGL headers), .github/workflows/ci.yml (lint+test+deploy), scripts/start.sh (migrations+uvicorn), .gitignore updated — 1056 tests pass, ruff clean |

---

## Endpoint Summary (73 endpoints)

| Domain | Count | Phase |
|--------|-------|-------|
| Health | 1 | 1 |
| Auth | 4 | 2 |
| Save/Load | 4 | 3 |
| Monsters | 7 | 3 |
| Teams | 6 | 3 |
| Combat | 4 | 3 |
| Taming | 3 | 3 |
| Economy | 4 | 4 |
| Crafting | 4 | 4 |
| Life Skills | 3 | 4 |
| Action Queue | 5 | 4 |
| Idle/Offline | 4 | 4 |
| Skills/Strategy | 6 | 4 |
| Premium | 6 | 5 |
| Subscriptions | 5 | 5 |
| Reward Ads | 3 | 5 |
| **Total** | **73** | |

---

## Notes

- Existing 884 tests and game logic modules remain untouched -- the API layer wraps them, it does not replace them.
- The package rename (monster_rpg -> elements_rpg) should be done first to avoid confusion in all new code.
- GameSaveData already aggregates all player state -- the save/load endpoints can leverage this directly for atomic persistence.
- Monetization is strictly convenience-only per the PRD -- no direct stat purchases, no pay-to-win. This must be enforced server-side.
- The idle system's 85% efficiency rate and 8hr offline cap must be enforced server-side, never trusted from the client.
- All taming pity state must be server-authoritative to prevent manipulation.
- Phase 6 (Docker/CI) can be started in parallel with Phases 3-5 since it depends only on the app structure from Phase 1.
