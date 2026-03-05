# Feature: Monster Survival RPG — Phase 3 Economy & Idle Systems

## Status
- **Phase**: implement (Phase 3 — Economy & Idle)
- **Status**: active
- **Progress**: 4/4 tasks complete
- **Last Updated**: 2026-03-04

## Feature Scope
Implement the economy and idle game systems on top of the Phase 1 foundation models and Phase 2 core systems:
- Idle System with fastest clear time tracking, BRPM calculation, 85% idle rate, 8hr offline cap
- Life Skills (Mining, Cooking, Strategy Training) with XP/leveling and resource yields
- Unified Action Queue with crafting, cooking, training actions, 2 base slots, queue management
- Economy Manager with materials/resources tracking, crafting recipes, gold/gem transactions

## Key PRD Specs

### Idle System (PRD Section 5)
- Each area tracks: **Fastest Clear Time**, **Resource Yield**, **Best Resource Rate Per Minute (BRPM)**
- **Idle Rate = 85% of Best Recorded BRPM**
- Idle gains cannot exceed best active performance
- Idle gains improve when player clears faster
- **Offline cap**: Base 8 hours, expandable via upgrades/subscription
- Gains formula: `Min(offline_duration, offline_cap_hours) * idle_rate`

### Life Skills (PRD Section 7)
- **MVP scope**: Mining, Cooking, Strategy Training
- All life skills **level permanently**
- Future skills (Phase 2+): Fishing, Foraging, Tailoring, Brewing, Woodcutting, Enhancing

### Unified Action Queue (PRD Section 8)
- **Single queue per player**
- Queue supports: Crafting, Cooking, Strategy Training, Skill Training
- **Base Slots: 2**
- Upgradeable: up to 6-8
- Subscription Bonus: +1 slot

### Economy / Monetization Specs (PRD Section 10)
- **Premium Currency: Gems** — used for team slot expansion, action queue expansion, offline cap expansion, inventory expansion, cosmetic purchases, convenience boosts
- **No direct stat purchases**
- Reward Ads (optional): Revive, +25% idle gains (temporary), bonus taming attempt, temporary resource boost
- Subscription tiers: Ad removal, +10% idle cap, +1 action slot, daily gems, exclusive cosmetics

## Tasks

### Phase 1 — Foundation (Complete)
- [x] `implementation-agent` | Configure pyproject.toml — fix project name/description, add dev deps (pytest, ruff, mypy, pydantic), add Ruff config section, remove unintentional datetime dep | complete
- [x] `implementation-agent` | Create src/monster_rpg/ directory structure with vertical slices (combat/, monsters/, idle/, economy/, skills/ with __init__.py and tests/) | complete
- [x] `implementation-agent` | Create base Pydantic v2 models (Monster, Skill, Area, Player) in appropriate modules with tests | complete
- [x] `implementation-agent` | Verify full setup — uv sync, ruff check, pytest all pass | complete

### Phase 1 — Review (Complete)
- [x] `review-agent` | Test verification and documentation review | complete
- [x] `blocking-pr-critic` | Final approval of Phase 1 | complete

### Phase 2 — Core Systems (Complete)
- [x] `implementation-agent` | Implement Combat Manager — auto-combat loop, damage calculation, HP tracking, turn-based resolution with speed priority | complete
- [x] `implementation-agent` | Implement Monster system — level/XP progression, bond system, equipped skills management, strategy profile per monster | complete
- [x] `implementation-agent` | Implement Skill system — skill leveling via usage, XP thresholds, milestone upgrades at levels 10/25/50 | complete
- [x] `implementation-agent` | Implement Strategy AI system — 5 base strategies with behavior modifiers, proficiency leveling, mastery unlock | complete
- [x] `implementation-agent` | Implement Taming system — capture rate formula (base_rate + food_bonus + skill_modifier), soft pity after 50 attempts | complete

### Phase 2 — Review (Complete)
- [x] `review-agent` | Test verification and code quality review | complete
- [x] `blocking-pr-critic` | Final approval of Phase 2 — 3 review fixes applied | complete

### Phase 3 — Economy & Idle (Implementation)
- [x] `implementation-agent` | Implement Idle system — fastest clear time tracking, BRPM calculation, 85% idle rate, 8hr offline cap, offline gains calculation | complete
- [x] `implementation-agent` | Implement Life Skills — Mining, Cooking, Strategy Training with XP/leveling, resource yields, permanent progression | complete
- [x] `implementation-agent` | Implement Unified Action Queue — crafting, cooking, training actions with 2 base slots, upgradeable to 6-8, queue management | complete
- [x] `implementation-agent` | Implement Economy Manager — materials/resources tracking, crafting recipes, gold/gem transactions, no direct stat purchases | complete

### Phase 3 — Review
- [ ] `review-agent` | Test verification and code quality review | pending
- [ ] `blocking-pr-critic` | Final approval of Phase 3 | pending

## Blockers
None

## Progress Log
| Timestamp | Agent | Task | Status | Notes |
|-----------|-------|------|--------|-------|
| 2026-03-04 | implementation-agent | Configure pyproject.toml | complete | Added pydantic v2, dev deps (pytest, ruff, mypy, pytest-cov), ruff/mypy/pytest config, removed erroneous datetime dep |
| 2026-03-04 | implementation-agent | Create src/monster_rpg/ directory structure | complete | Vertical slice architecture with combat/, monsters/, idle/, economy/, skills/ modules, each with tests/. 11 tests passing, ruff clean. |
| 2026-03-04 | implementation-agent | Create base Pydantic v2 models | complete | Monster, MonsterSpecies, StatBlock, Element, Rarity, Skill, SkillType, StrategyType, StrategyProfile, Area, AreaDifficulty, Player models with 69 tests passing, ruff clean. |
| 2026-03-04 | implementation-agent | Verify full setup | complete | Added hatchling build-system to pyproject.toml for editable install. Package installs via uv sync, import works, 69 tests pass, ruff clean. Mypy has 27 errors (all dict unpacking into Pydantic models — known strict mode issue, non-blocking). |
| 2026-03-04 | review-agent | Test verification and documentation review | complete | SHIP-READY. 69 tests pass, 99% coverage, ruff clean, no circular imports, no security issues, PRD constants match. 1 MEDIUM finding: README.md empty. 6 LOW findings: mypy test helper types, strategy name deviations from PRD, action_queue_slots max (5 vs PRD 6-8), no Player.level upper bound, no Monster.current_hp upper bound, no __init__.py re-exports. |
| 2026-03-04 | implementation-agent | Fix 3 blocking PR review issues | complete | Added min_length=1 to all ID fields (species_id, monster_id, skill_id, area_id, player_id) with validation tests. Renamed combat/damage_calc.py to combat/strategy.py and updated all imports. Replaced int() with round() in Monster.effective_stats(). 74 tests pass, ruff clean. |
| 2026-03-04 | implementation-agent | Implement Combat Manager | complete | damage_calc.py with element chart, STAB, skill level bonus, RPG damage formula. manager.py with CombatManager: speed-based turn order, lowest-HP targeting, auto-combat loop. 48 new tests (122 total), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Monster system | complete | xp_for_level() power-curve formula, gain_experience() with multi-level and max cap, gain_bond() with 100 cap, bond multiplier in effective_stats(), equip/unequip/can_learn skill management, max_hp(). 33 new tests (155 total), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Skill system | complete | skill_xp_for_level() with power-curve formula, gain_experience() with multi-level and max cap, SkillMilestone model with unlocked/next methods, effective_power() with 2% per-level bonus, effective_cooldown() with 1% per-level reduction (min 0.5s). Skill constants in config.py. 36 new tests (185 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Strategy AI system | complete | Updated StrategyType enum to PRD's 5 strategies (ATTACK_NEAREST, FOLLOW_PLAYER, DEFENSIVE, AGGRESSIVE, HEAL_LOWEST). Added gain_experience()/check_mastery() to StrategyProfile with XP formula int(200*level^1.2). Created strategy_ai.py with StrategyBehavior dataclass, behavior definitions, and select_target_by_strategy(). 42 new/updated tests (227 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Taming system | complete | BASE_CAPTURE_RATES per rarity, FoodItem model with favorite elements, TamingTracker for per-species pity tracking, calculate_pity_bonus() with soft pity after 50 attempts, calculate_tame_chance() with HP modifier/food/skill bonuses, attempt_tame() integration function. 42 new tests (269 total passing), ruff clean. |
| 2026-03-04 | review-agent | Phase 2 code quality review | complete | SHIP-READY. 269 tests pass, 99% coverage (5 lines missed), ruff check + format clean. 1 fix applied: acknowledged unused proficiency param in strategy_ai.py with TODO. No blockers, no security issues. 3 MEDIUM findings (proficiency not wired, unreachable fallback in strategy_ai, combat manager lines 183/187 untested). 2 LOW findings (skill gain_experience rejects 0 xp unlike monster version, combat manager doesn't integrate strategy AI targeting). |
| 2026-03-04 | implementation-agent | Fix 3 blocking Phase 2 review issues | complete | (1) Skill.gain_experience() now subtracts XP per level-up matching Monster/Strategy pattern. (2) damage_calc uses skill.effective_power() — removed duplicate skill_bonus multiplier. (3) Removed unused SKILL_MILESTONE_LEVELS constant. 269 tests pass, ruff clean. |
| 2026-03-04 | implementation-agent | Implement Idle system | complete | IdleTracker with per-area best clear time recording, BRPM calculation, 85% idle efficiency rate. OfflineGainsResult with 8hr cap, configurable reward rates. AreaClearRecord with validation. 32 new tests (301 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Unified Action Queue | complete | ActionQueue with QueuedAction model, 5 ActionTypes (craft/cook/mine/train_strategy/train_skill), auto-start on add, advance/cancel/clear operations, 2 base slots expandable to 8. 38 new tests (413 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Economy Manager | complete | Material, CraftingRecipe, Inventory models with full CRUD. EconomyManager with gold/gem spend/earn and CurrencyTransaction logging. Inventory supports add/remove/has_materials, can_craft/execute_craft functions. 62 economy tests (433 total passing), ruff clean. |
