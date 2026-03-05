# ElementsRPG — Backend

Hybrid Active + Idle ElementsRPG backend. Auto-combat survival, monster collection/taming, persistent skill progression, strategy AI customization, life skills economy.

## Tech Stack

- Python 3.11+
- Pydantic v2 (data models & validation)
- UV (package management)

## Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Lint & format
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run mypy src/elements_rpg/
```

## Project Structure

```
src/elements_rpg/
├── main.py          # Entry point
├── config.py        # Game constants
├── player.py        # Player model
├── combat/          # Combat system & strategy AI
├── monsters/        # Monster models & taming
├── idle/            # Idle/offline progression
├── economy/         # Areas, crafting, resources
└── skills/          # Skill progression system
```

Each module follows vertical slice architecture with co-located tests.

## Core Systems

**Phase 2 Implementation Complete:**
- **Combat Manager**: Full auto-combat system with damage calculations, critical hits, status effects
- **Monster Models**: Leveling, bonding, equipped skills, passive traits, stat evolution
- **Skill System**: 4-skill slots, usage-based leveling, milestone upgrades with Pydantic validation
- **Strategy AI**: 5 base strategies (Aggressive, Defensive, Balanced, Healing, Random) with proficiency tracking and mastery progression
- **Taming System**: Dynamic base rates, food & skill modifiers, soft pity mechanics

**Phase 3 Implementation Complete:**
- **Idle System**: Offline progression with fastest clear time tracking, Base Runs Per Minute (BRPM) calculation, 85% idle rate, 8-hour offline cap
- **Life Skills**: Mining, Cooking, and Strategy Training skill progression with proficiency levels
- **Unified Action Queue**: 2-slot action queue supporting crafting, cooking, and strategy training tasks
- **Economy Manager**: Material inventory tracking, crafting recipes, resource management system

**Phase 4 Implementation Complete:**
- **Team System**: Up to 6 monsters per team with composition validation and team-level stats
- **Area System**: 2 MVP areas (Forest, Desert) with exclusive monsters, materials, and difficulty scaling
- **Bestiary**: 12 MVP monsters with unique skills, passive traits, and stat distributions
- **Skill Catalog**: 28 unique skills distributed across monsters with specialized abilities

**Phase 5 Implementation Complete:**
- **Premium Currency**: Gem system with purchase tracking and balance management
- **Reward Ads**: Optional ad hooks for combat revive, idle boost, and taming bonus
- **Subscriptions**: Tiered subscription system with benefit tracking and renewal management
- **Save/Load System**: Cloud-ready serialization with versioning support and full game state persistence

## Project Status

All 5 phases complete:
- **Phase 1 — Foundation**: Python project structure, Pydantic models, development setup
- **Phase 2 — Core Systems**: Combat, monsters, skills, strategy AI, taming
- **Phase 3 — Economy & Idle**: Offline progression, life skills, action queue, resource management
- **Phase 4 — Team & Areas**: Teams, 2 areas, 12 monsters, 28 skills
- **Phase 5 — Monetization & Polish**: Gems, reward ads, subscriptions, save/load

## Development

- 884 tests with 99% coverage
- Ruff for linting (line-length=100, double quotes)
- Mypy strict mode for type checking
