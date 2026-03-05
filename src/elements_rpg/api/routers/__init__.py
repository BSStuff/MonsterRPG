"""API router registry -- exports all domain routers for inclusion in the app."""

from elements_rpg.api.routers.auth import router as auth_router
from elements_rpg.api.routers.combat import router as combat_router
from elements_rpg.api.routers.crafting import router as crafting_router
from elements_rpg.api.routers.economy import router as economy_router
from elements_rpg.api.routers.health import router as health_router
from elements_rpg.api.routers.idle import router as idle_router
from elements_rpg.api.routers.monsters import router as monsters_router
from elements_rpg.api.routers.players import router as players_router
from elements_rpg.api.routers.premium import router as premium_router
from elements_rpg.api.routers.saves import router as saves_router
from elements_rpg.api.routers.skills import router as skills_router
from elements_rpg.api.routers.taming import router as taming_router
from elements_rpg.api.routers.teams import router as teams_router

ALL_ROUTERS = [
    health_router,
    auth_router,
    players_router,
    saves_router,
    monsters_router,
    teams_router,
    combat_router,
    taming_router,
    skills_router,
    economy_router,
    crafting_router,
    idle_router,
    premium_router,
]

__all__ = [
    "ALL_ROUTERS",
    "auth_router",
    "combat_router",
    "crafting_router",
    "economy_router",
    "health_router",
    "idle_router",
    "monsters_router",
    "players_router",
    "premium_router",
    "saves_router",
    "skills_router",
    "taming_router",
    "teams_router",
]
