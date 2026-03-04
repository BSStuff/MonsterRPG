# Monster Survival RPG - CLAUDE.md

## Project Overview
- **Project Name**: Monster Survival RPG
- **Description**: Hybrid Active + Idle Monster Survival RPG — auto-combat survival, monster collection/taming, persistent skill progression, strategy AI customization, life skills economy, convenience-based monetization. Unity WebGL (Phase 1), mobile (Phase 2). Python backend for game services.
- **Tech Stack**: Unity/C# (game client), Python 3.11 + UV (backend services), WebGL target
- **Last Updated**: 2026-03-04

---

## Work Principles

### Autonomy
Full permissions granted. Act decisively without asking — read, write, edit, execute freely.

### Git Discipline
- **Commit after every meaningful change** — never batch unrelated work
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Commit message = what changed + why (not how)

### Branch Strategy
- `main` — Production-ready code
- `develop` — Integration branch for features
- `feature/*` — New features
- `fix/*` — Bug fixes
- `docs/*` — Documentation updates
- `refactor/*` — Code refactoring
- `test/*` — Test additions or fixes

### Documentation
- Update README.md when adding features or changing setup
- Update this file's session log after work sessions
- Keep docs in sync with code changes

### Thinking
Extended thinking is enabled. Use deep reasoning for complex architectural decisions, difficult bugs, and multi-file changes.

### Task Tracking (TodoWrite)
**ALWAYS use TodoWrite** to track tasks. This is non-negotiable for anything beyond trivial single-step work.

**When to use TodoWrite:**
- Multi-step tasks (3+ steps)
- Bug fixes requiring investigation
- Feature implementations
- Any work where progress tracking helps
- When the user provides multiple requests

**How to use it:**
1. **Before starting**: Break down the work into discrete todos
2. **During work**: Mark each todo `in_progress` before starting, `completed` when done
3. **One at a time**: Only ONE todo should be `in_progress` at any moment
4. **Immediately**: Mark todos complete the moment they're done — don't batch

**Syncing with CLAUDE.md:**
- When creating TodoWrite tasks, also add them to "Current Task Queue" below
- Mark tasks complete in BOTH places
- This keeps the project documentation up-to-date with actual work

**Anti-patterns to avoid:**
- Starting work without creating todos first
- Having multiple todos `in_progress` simultaneously
- Batching completions at the end
- Skipping TodoWrite for "simple" multi-step tasks

---

## When to Use Agents

**Explore agent**: Codebase investigation, finding files, understanding architecture

**Parallel agents**: Independent tasks that don't conflict

**Background execution**: Long-running operations (tests, builds)

**Sequential chaining**: When second task depends on first

---

## Planning Mode (Automatic)

**Automatically enter planning mode** when ANY of these conditions apply:
- Multi-file changes (3+ files affected)
- Architectural decisions
- Unclear or evolving requirements
- Risk mitigation on core systems
- New feature implementation
- Refactoring existing functionality

**Do NOT ask** whether to enter planning mode — just enter it when conditions are met.

Planning mode flow: read-only exploration → create plan → get approval → execute.

**Skip planning mode** only for:
- Single-file bug fixes
- Typo corrections
- Simple config changes
- Tasks with explicit step-by-step instructions from user

---

## Ralph Wiggum Loop (Autonomous Work Mode)

Ralph loops enable persistent, autonomous work on large tasks. When active, continue iterating until completion criteria are met or the loop is cancelled.

### Starting a Ralph Loop
- Start: `/ralph-loop:ralph-loop`
- Cancel: `/ralph-loop:cancel-ralph`
- Help: `/ralph-loop:help`

### Core Behaviors During Ralph Loop

**1. Work Incrementally** — Complete one sub-task at a time, verify before moving on.

**2. Commit Frequently** — After each meaningful completion.

**3. Self-Correct Relentlessly**
```
Loop:
  1. Implement/fix
  2. Run tests
  3. If tests fail → read error, fix, go to 1
  4. Run linter
  5. If lint errors → fix, go to 1
  6. Commit
  7. Continue to next task
```

**4. Track Progress** — Update the session log below.

**5. Completion Phrase = Contract** — Only output when ALL requirements done, ALL tests pass, ALL linting passes, changes committed.

---

## Code Standards

### Before Writing
- Read existing code in the area you're modifying
- Follow existing patterns and conventions

### During Implementation
- Keep changes focused and minimal
- Don't over-engineer
- Write tests for new functionality

### After Implementation
- Run tests
- Update docs if needed
- Commit with descriptive message

---

## Code Structure & Modularity

### File and Function Limits
- **No file longer than 500 lines**. Refactor by splitting into modules.
- **Functions under 50 lines** with single, clear responsibility.
- **Classes under 100 lines** representing a single concept.
- **Line length max 100 characters** (Ruff rule in pyproject.toml)

### Project Architecture (Python Backend)

Follow strict vertical slice architecture with tests next to code:

```
src/monster_rpg/
    __init__.py
    main.py
    config.py
    tests/
        test_main.py
    conftest.py

    # Core game systems
    combat/
        __init__.py
        manager.py
        damage_calc.py
        tests/
            test_manager.py
            test_damage_calc.py

    monsters/
        __init__.py
        models.py
        taming.py
        tests/
            test_models.py
            test_taming.py

    idle/
        __init__.py
        tracker.py
        offline_gains.py
        tests/
            test_tracker.py
            test_offline_gains.py

    economy/
        __init__.py
        manager.py
        crafting.py
        tests/
            test_manager.py
            test_crafting.py

    skills/
        __init__.py
        progression.py
        strategy_ai.py
        tests/
            test_progression.py
            test_strategy_ai.py
```

---

## Development Environment

### UV Package Management

```bash
# Sync dependencies
uv sync

# Add a package (NEVER edit pyproject.toml dependencies directly)
uv add requests

# Add development dependency
uv add --dev pytest ruff mypy

# Remove a package
uv remove requests

# Run commands in the environment
uv run python script.py
uv run pytest
uv run ruff check .
```

### Development Commands

```bash
# Run all tests
uv run pytest

# Run specific tests with verbose output
uv run pytest tests/test_module.py -v

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Type checking
uv run mypy src/
```

---

## Style & Conventions

### Python Style Guide
- **PEP8** with line length 100 (Ruff)
- Double quotes for strings
- Trailing commas in multi-line structures
- **Always use type hints** for function signatures and class attributes
- **Pydantic v2** for data validation
- **Google-style docstrings** for public functions/classes

### Naming Conventions
- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes/methods**: `_leading_underscore`

---

## Testing Strategy

- Write tests before implementing features (TDD)
- Use pytest with fixtures
- Keep tests fast and isolated
- Test edge cases and error conditions
- Aim for 80%+ coverage on critical paths
- Tests live next to the code they test

---

## Hooks Awareness

This project may have hooks that auto-format code after writes. If a tool call behaves unexpectedly, hooks are likely the cause. Continue working.

---

## Session Log

| Date | Tasks Completed | Files Changed | Notes |
|------|-----------------|---------------|-------|
| 2026-03-04 | Project init, CLAUDE.md + KNOWLEDGE_BASE.md created | CLAUDE.md, .claude/KNOWLEDGE_BASE.md | Fresh project setup |
| 2026-03-04 | Phase 1 Foundation complete — pyproject.toml, project structure, Pydantic models, review fixes | pyproject.toml, src/monster_rpg/** (36+ files), README.md, .claude/plan.md | 74 tests passing, 99% coverage, all review issues resolved |

---

## Current Task Queue

### Active Ralph Loop
**Status**: Not Active
**Completion Phrase**: -

### Pending Tasks

#### Phase 1 — Foundation
- [x] Set up Python project structure (src/monster_rpg/ vertical slices)
- [x] Configure pyproject.toml with dev dependencies (pytest, ruff, mypy)
- [x] Set up Ruff linting config (line-length=100, double quotes)
- [x] Create base Pydantic models for Monster, Skill, Area, Player

#### Phase 2 — Core Systems
- [ ] Implement Combat Manager (auto-combat, damage calc, HP/stats)
- [ ] Implement Monster models (level, bond, 4 skills, passive trait, stats, strategy profile)
- [ ] Implement Skill system (4 equipped skills, leveling via usage, milestone upgrades)
- [ ] Implement Strategy AI system (5 base strategies, proficiency levels, mastery)
- [ ] Implement Taming system (base rate, food bonus, skill modifier, soft pity)

#### Phase 3 — Economy & Idle
- [ ] Implement Idle system (fastest clear time, BRPM, 85% idle rate, 8hr offline cap)
- [ ] Implement Life Skills (Mining, Cooking, Strategy Training — MVP scope)
- [ ] Implement Unified Action Queue (crafting, cooking, training — 2 base slots)
- [ ] Implement Economy Manager (materials, crafting, resource tracking)

#### Phase 4 — Team & Areas
- [ ] Implement Team system (up to 6 monsters, composition logic)
- [ ] Create 2 MVP Areas with exclusive monsters/materials and difficulty scaling
- [ ] Design and implement 12 MVP Monsters with unique skills and traits

#### Phase 5 — Monetization & Polish
- [ ] Implement Premium Currency (Gems) system
- [ ] Implement optional Reward Ads hooks (revive, idle boost, taming bonus)
- [ ] Implement Subscription tier logic
- [ ] Save/Load system (cloud-ready serialization)

**Note for Claude Code CLI**:
- Update this section as you work on tasks
- Mark tasks complete using `[x]` when done
- Add new tasks as they come up

---

## Implementation Plans

<!-- Document plans before major implementations -->

---

## Notes & Decisions

- PRD specifies Unity/C# for game client (WebGL → Mobile), Python backend for game services
- MVP scope: 2 areas, 12 monsters, 3 life skills, 1 action queue, 1 team
- No PvP, guilds, or battle pass in Phase 1
- Monetization is convenience-only, no direct stat purchases
- Idle rate = 85% of best recorded BRPM

---

## GitHub Flow Workflow Summary

```
main (protected) ←── PR ←── feature/your-feature
```

### Daily Workflow:
1. `git checkout main && git pull origin main`
2. `git checkout -b feature/new-feature`
3. Make changes + tests
4. `git push origin feature/new-feature`
5. Create PR → Review → Merge to main

---

_This document is a living guide. Update it as the project evolves._
