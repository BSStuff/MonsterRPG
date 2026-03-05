# Monster Survival RPG — Backend

Hybrid Active + Idle Monster Survival RPG backend. Auto-combat survival, monster collection/taming, persistent skill progression, strategy AI customization, life skills economy.

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
uv run mypy src/monster_rpg/
```

## Project Structure

```
src/monster_rpg/
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

## Development

- 269 tests with 99% coverage
- Ruff for linting (line-length=100, double quotes)
- Mypy strict mode for type checking
