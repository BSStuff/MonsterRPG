"""API router registry — collects all domain routers for inclusion in the app."""

from fastapi import APIRouter

# Domain routers will be imported here as they are implemented.
# Each router module should export a `router` variable (APIRouter instance).
#
# Example (uncomment as routers are created):
#   from elements_rpg.api.routers.auth import router as auth_router
#
# For now, we expose a list that app.py iterates over.

_ROUTER_MODULES: list[tuple[APIRouter, str, str]] = []
# Entries are (router_instance, prefix, tag)


def _try_import() -> list[tuple[APIRouter, str, str]]:
    """Attempt to import all domain routers, skipping any that don't exist yet.

    Returns a list of (router, prefix, tag) tuples for all successfully imported routers.
    """
    router_specs: list[tuple[str, str, str]] = [
        ("elements_rpg.api.routers.auth", "/auth", "Auth"),
        ("elements_rpg.api.routers.combat", "/combat", "Combat"),
        ("elements_rpg.api.routers.monsters", "/monsters", "Monsters"),
        ("elements_rpg.api.routers.teams", "/teams", "Teams"),
        ("elements_rpg.api.routers.taming", "/taming", "Taming"),
        ("elements_rpg.api.routers.economy", "/economy", "Economy"),
        ("elements_rpg.api.routers.crafting", "/crafting", "Crafting"),
        ("elements_rpg.api.routers.life_skills", "/life-skills", "Life Skills"),
        ("elements_rpg.api.routers.action_queue", "/action-queue", "Action Queue"),
        ("elements_rpg.api.routers.idle", "/idle", "Idle"),
        ("elements_rpg.api.routers.skills", "/skills", "Skills"),
        ("elements_rpg.api.routers.premium", "/premium", "Premium"),
        ("elements_rpg.api.routers.subscriptions", "/subscriptions", "Subscriptions"),
        ("elements_rpg.api.routers.ads", "/ads", "Ads"),
        ("elements_rpg.api.routers.save_load", "/save", "Save/Load"),
    ]

    loaded: list[tuple[APIRouter, str, str]] = []
    for module_path, prefix, tag in router_specs:
        try:
            import importlib

            mod = importlib.import_module(module_path)
            router: APIRouter = mod.router
            loaded.append((router, prefix, tag))
        except (ImportError, AttributeError):
            # Router not yet implemented — skip silently during scaffold phase
            pass

    return loaded


def get_all_routers() -> list[tuple[APIRouter, str, str]]:
    """Return all available domain routers as (router, prefix, tag) tuples."""
    return _try_import()
