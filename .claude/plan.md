# Feature: Monster Survival RPG — Phase 5 Monetization & Polish

## Status
- **Phase**: done (Phase 5 — Monetization & Polish)
- **Status**: complete
- **Progress**: 4/4 tasks complete + review fixes applied
- **Last Updated**: 2026-03-04

## Feature Scope
Implement monetization systems and save/load persistence on top of Phases 1-4:
- Premium Currency (Gems) system with gem packages, gem-purchasable upgrades, price catalog
- Reward Ads hooks for revive, idle boost, taming bonus, resource boost with cooldowns/limits
- Subscription tier logic with monthly benefits (extra queue slot, increased offline cap, cosmetics)
- Save/Load system with cloud-ready serialization of all player data

## Key PRD Specs

### Premium Currency — Gems (PRD Section 10.2)
- **Used for**: Team slot expansion, Action queue expansion, Offline cap expansion, Inventory expansion, Cosmetic purchases, Convenience boosts
- **No direct stat purchases** — convenience only
- Gem packages (purchasable bundles of gems at different price points)
- Price catalog mapping gem costs to each upgrade type

### Reward Ads (PRD Section 10.1)
- **Optional only** — no forced pop-ups
- Ad reward types:
  - **Revive**: Restore team after wipe
  - **+25% idle gains**: Temporary boost to idle rate
  - **Bonus taming attempt**: Extra tame chance after failure
  - **Temporary resource boost**: Increased drop rates
- Must include cooldowns and daily limits per ad type

### Subscription Tiers (PRD Section 10.3)
- **Duration options**: 30-Day / 90-Day / 1-Year
- **Benefits**:
  - Ad removal
  - +10% idle cap (8hr base -> 8.8hr)
  - +1 action queue slot
  - Daily gem stipend
  - Exclusive cosmetics
- **Power advantage capped** at minor convenience levels

### Save/Load System (PRD Section 12)
- Cloud-ready serialization
- Must persist ALL player data: monsters (level, bond, skills, strategy profiles), inventory (materials, gold, gems), progress (area clears, BRPM records, life skill levels), economy (transaction history, crafting state), team composition, action queue state, subscription/ad state
- Versioned save format for future migration support

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

### Phase 3 — Economy & Idle (Complete)
- [x] `implementation-agent` | Implement Idle system — fastest clear time tracking, BRPM calculation, 85% idle rate, 8hr offline cap, offline gains calculation | complete
- [x] `implementation-agent` | Implement Life Skills — Mining, Cooking, Strategy Training with XP/leveling, resource yields, permanent progression | complete
- [x] `implementation-agent` | Implement Unified Action Queue — crafting, cooking, training actions with 2 base slots, upgradeable to 6-8, queue management | complete
- [x] `implementation-agent` | Implement Economy Manager — materials/resources tracking, crafting recipes, gold/gem transactions, no direct stat purchases | complete

### Phase 3 — Review (Complete)
- [x] `review-agent` | Test verification and code quality review | complete
- [x] `blocking-pr-critic` | Final approval of Phase 3 — 5 review fixes applied | complete

### Phase 4 — Team & Areas (Complete)
- [x] `implementation-agent` | Implement Team system — team composition up to 6 monsters, team management (add/remove/reorder), team validation, suggested composition roles (Tank/Off-Tank/DPS/Support/Flex), multiple teams unlockable via upgrades | complete
- [x] `implementation-agent` | Create 2 MVP Areas with exclusive monsters/materials, difficulty scaling, area-specific drop tables, taming base rates, idle tracking integration | complete
- [x] `implementation-agent` | Design and implement 12 MVP Monsters with unique skills, traits, elements, stats, taming difficulties, and area assignments | complete

### Phase 4 — Review (Complete)
- [x] `review-agent` | Test verification and code quality review | complete
- [x] `blocking-pr-critic` | Final approval of Phase 4 — 3 review fixes applied | complete

### Phase 5 — Monetization & Polish (Implementation)
- [x] `implementation-agent` | Implement Premium Currency (Gems) system — gem packages, gem-purchasable upgrades (queue slots, offline cap, inventory), price catalog | complete
- [x] `implementation-agent` | Implement Reward Ads hooks — revive, idle boost (+25%), taming bonus, resource boost, with cooldowns and limits | complete
- [x] `implementation-agent` | Implement Subscription tier logic — monthly sub with benefits (extra queue slot, increased offline cap, cosmetics) | complete
- [x] `implementation-agent` | Implement Save/Load system — cloud-ready serialization of all player data (monsters, inventory, progress, economy) | complete

### Phase 5 — Review (Complete)
- [x] `review-agent` | Test verification and code quality | complete
- [x] `blocking-pr-critic` | Final approval of Phase 5 — 4 review fixes + currency dedup applied | complete

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
| 2026-03-04 | review-agent | Phase 2 code quality review | complete | SHIP-READY. 269 tests pass, 99% coverage, ruff check + format clean. 1 fix applied: acknowledged unused proficiency param in strategy_ai.py with TODO. No blockers, no security issues. 3 MEDIUM findings (proficiency not wired, unreachable fallback in strategy_ai, combat manager lines 183/187 untested). 2 LOW findings (skill gain_experience rejects 0 xp unlike monster version, combat manager doesn't integrate strategy AI targeting). |
| 2026-03-04 | implementation-agent | Fix 3 blocking Phase 2 review issues | complete | (1) Skill.gain_experience() now subtracts XP per level-up matching Monster/Strategy pattern. (2) damage_calc uses skill.effective_power() — removed duplicate skill_bonus multiplier. (3) Removed unused SKILL_MILESTONE_LEVELS constant. 269 tests pass, ruff clean. |
| 2026-03-04 | implementation-agent | Implement Idle system | complete | IdleTracker with per-area best clear time recording, BRPM calculation, 85% idle efficiency rate. OfflineGainsResult with 8hr cap, configurable reward rates. AreaClearRecord with validation. 32 new tests (301 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Unified Action Queue | complete | ActionQueue with QueuedAction model, 5 ActionTypes (craft/cook/mine/train_strategy/train_skill), auto-start on add, advance/cancel/clear operations, 2 base slots expandable to 8. 38 new tests (413 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Implement Economy Manager | complete | Material, CraftingRecipe, Inventory models with full CRUD. EconomyManager with gold/gem spend/earn and CurrencyTransaction logging. Inventory supports add/remove/has_materials, can_craft/execute_craft functions. 62 economy tests (433 total passing), ruff clean. |
| 2026-03-04 | implementation-agent | Fix 5 blocking Phase 3 review issues | complete | (1) Enum pattern confirmed correct (StrEnum). (2) expand_slots rejects zero/negative. (3) EconomyManager owns gold/gems as Pydantic BaseModel. (4) execute_craft atomic with snapshot/rollback. (5) model_validators on CraftingRecipe/QueuedAction/LifeSkillAction for material qty >= 1, speed_bonus clamped to 0.1. 441 tests pass, ruff clean. |
| 2026-03-04 | implementation-agent | Implement Team system | complete | Team, TeamSlot, TeamRole models with add/remove/reorder/set_role/get_by_role/get_team_monsters. Validators for max size, duplicate monsters, duplicate positions. 42 new tests (483 total passing), ruff clean. |
