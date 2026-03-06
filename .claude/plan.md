# Project Plan: ElementsRPG Element System Redesign

## Status: Phase 1-3 Complete
## Last Updated: 2026-03-05

---

## Previous Work Summary (Deployment & API Layer -- COMPLETE)

All 7 deployment phases completed: FastAPI backend with 73 endpoints, Supabase Auth + PostgreSQL, Docker/Render/Vercel deployment, GitHub Actions CI/CD, 1068 tests passing. Full details in git history and CLAUDE.md session log.

---

## Overview

Redesign the element/type system from 5 elements to 10, add dual typing for monsters, create a balanced type effectiveness chart, and update all existing content. This touches the core game logic layer, the content definitions (bestiary, skills, areas), the API/service layer, and the save/load system.

**Current State**: 5 elements (fire, water, earth, wind, neutral). Single-typed monsters. Simple 1.5x/0.5x chart with 8 entries. No immunities.

**Target State**: 10 elements (water, fire, grass, electric, wind, ground, rock, dark, light, ice). Dual typing support. Full 10x10 effectiveness matrix with 2x/0.5x/0x multipliers. Backward-compatible saves.

---

## New Element Set

| Old Element | Mapping / Notes |
|-------------|----------------|
| FIRE | Retained as FIRE |
| WATER | Retained as WATER |
| EARTH | Split into GRASS, GROUND, ROCK depending on monster/skill flavor |
| WIND | Retained as WIND |
| NEUTRAL | Remapped to DARK, LIGHT, ELECTRIC, or ICE depending on monster/skill flavor |

New elements: **WATER, FIRE, GRASS, ELECTRIC, WIND, GROUND, ROCK, DARK, LIGHT, ICE**

---

## Type Effectiveness Chart (10x10)

Multipliers: 2.0 = super effective, 0.5 = not effective, 0.0 = immune, 1.0 = neutral (omitted)

| Attacking -> | Water | Fire | Grass | Electric | Wind | Ground | Rock | Dark | Light | Ice |
|---|---|---|---|---|---|---|---|---|---|---|
| **Water** | 0.5 | 2.0 | 0.5 | 1.0 | 1.0 | 2.0 | 2.0 | 1.0 | 1.0 | 1.0 |
| **Fire** | 0.5 | 0.5 | 2.0 | 1.0 | 2.0 | 1.0 | 0.5 | 1.0 | 1.0 | 2.0 |
| **Grass** | 2.0 | 0.5 | 0.5 | 1.0 | 0.5 | 2.0 | 2.0 | 1.0 | 1.0 | 0.5 |
| **Electric** | 2.0 | 1.0 | 0.5 | 0.5 | 2.0 | **0.0** | 1.0 | 1.0 | 1.0 | 1.0 |
| **Wind** | 1.0 | 0.5 | 2.0 | 0.5 | 1.0 | 2.0 | 0.5 | 1.0 | 1.0 | 1.0 |
| **Ground** | 1.0 | 2.0 | 0.5 | 2.0 | 1.0 | 1.0 | 2.0 | 1.0 | 1.0 | 0.5 |
| **Rock** | 1.0 | 2.0 | 0.5 | 1.0 | 2.0 | 0.5 | 1.0 | 1.0 | 1.0 | 2.0 |
| **Dark** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 2.0 | 1.0 |
| **Light** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 2.0 | 0.5 | 1.0 |
| **Ice** | 0.5 | 0.5 | 2.0 | 1.0 | 2.0 | 2.0 | 0.5 | 1.0 | 1.0 | 0.5 |

**Balance summary per type**:
- Each type has 2-4 super effective matchups
- Each type has 2-4 not-effective matchups (including self-resist)
- 1 immunity: Ground is immune to Electric
- Dark/Light are mutual: each is super effective against the other, resists itself
- No single type dominates; all have clear offensive and defensive trade-offs

**Dual typing rule**: For a dual-typed defender, multiply both matchup multipliers. Examples:
- Electric vs Water/Ground defender: 2.0 * 0.0 = 0.0 (immune)
- Fire vs Grass/Ice defender: 2.0 * 2.0 = 4.0 (double super effective)
- Water vs Fire/Rock defender: 2.0 * 2.0 = 4.0
- Fire vs Water/Ground defender: 0.5 * 1.0 = 0.5

---

## Files Affected

### Core Game Logic (must change)
| File | Change Description |
|------|-------------------|
| `src/elements_rpg/monsters/models.py` | Update Element enum (5 -> 10); add `types` field to MonsterSpecies as `tuple[Element, Element \| None]`; keep deprecated `element` property for backward compat |
| `src/elements_rpg/combat/damage_calc.py` | Replace ELEMENT_CHART with 10x10 matrix; update `get_element_multiplier()` for dual-type defenders; update STAB for dual-typed attackers |
| `src/elements_rpg/skills/progression.py` | No structural change (Skill already has `element: Element` field) -- just needs to work with new enum values |

### Content Definitions (must change)
| File | Change Description |
|------|-------------------|
| `src/elements_rpg/monsters/bestiary.py` | Reassign all 12 monsters to new elements; some get dual types; update `element` -> `types` field |
| `src/elements_rpg/monsters/skill_catalog.py` | Reassign all skills from earth/fire/water to appropriate new elements (grass/ground/rock/ice/etc.) |
| `src/elements_rpg/monsters/skill_catalog_extended.py` | Reassign wind/neutral skills to wind/dark/light/electric/ice |
| `src/elements_rpg/economy/areas.py` | No element references in area definitions (monsters referenced by ID) -- likely no change |

### API / Service Layer (may change)
| File | Change Description |
|------|-------------------|
| `src/elements_rpg/services/monster_service.py` | Update response serialization (line ~297 exposes `species.element.value`) to expose `types` |
| `src/elements_rpg/services/combat_service.py` | No direct element references -- delegates to CombatManager/damage_calc |
| `src/elements_rpg/db/models/monster.py` | No change needed (stores species_id, not element directly) |
| `src/elements_rpg/db/converters.py` | Update if it maps element fields |

### Save/Load
| File | Change Description |
|------|-------------------|
| `src/elements_rpg/save_load.py` | Bump SAVE_FORMAT_VERSION to 2; add migration logic for v1 saves (map old elements to new) |

### Tests (~86 files reference Element)
| Category | Key Test Files |
|----------|---------------|
| Core | `combat/tests/test_damage_calc.py`, `monsters/tests/test_models.py`, `monsters/tests/test_bestiary.py` |
| Content | `monsters/tests/test_skill_catalog.py` |
| API | `api/tests/test_monsters.py`, `api/tests/test_combat.py`, `api/tests/test_e2e.py` |
| Services | `services/tests/test_combat_service.py` |

---

## Monster Redesign Plan (12 monsters -> new elements + dual types)

### Area 1: Verdant Meadows

| Monster | Old Element | New Types | Rationale |
|---------|------------|-----------|-----------|
| Leaflet | Earth | Grass | Plant monster, pure grass |
| Ember Pup | Fire | Fire | Stays pure fire |
| Breeze Sprite | Wind | Wind / Light | Sprite with light affinity |
| Pebble Crab | Earth | Rock / Ground | Crab with shell = rock, lives on ground |
| Dewdrop Slime | Water | Water | Stays pure water |
| Meadow Fox | Wind | Wind / Electric | Fast fox with electric speed |

### Area 2: Crystal Caverns

| Monster | Old Element | New Types | Rationale |
|---------|------------|-----------|-----------|
| Crystal Bat | Wind | Dark / Wind | Cave bat, dark affinity |
| Magma Wyrm | Fire | Fire / Ground | Magma = fire + ground |
| Aqua Serpent | Water | Water / Ice | Deep water serpent with ice |
| Shadow Moth | Neutral | Dark | Pure dark creature |
| Geo Golem | Earth | Rock / Ground | Golem = rock + ground |
| Prism Fairy | Neutral | Light | Pure light creature |

**Dual-type count**: 6 single-typed, 6 dual-typed (balanced mix)

---

## Skill Reassignment Plan (28 skills)

### Old Earth Skills -> Grass / Ground / Rock

| Skill | Old Element | New Element | Rationale |
|-------|-----------|-------------|-----------|
| Vine Whip | Earth | Grass | Plant-based attack |
| Root Bind | Earth | Grass | Plant roots |
| Leaf Shield | Earth | Grass | Leaf-based defense |
| Nature Heal | Earth | Grass | Nature/plant healing |
| Rock Slam | Earth | Rock | Rock-based attack |
| Stone Wall | Earth | Rock | Stone defense |
| Earthquake | Earth | Ground | Ground-shaking AoE |
| Fortify | Earth | Rock | Hardening defense |

### Old Fire Skills -> Fire (mostly unchanged)

| Skill | Old Element | New Element | Rationale |
|-------|-----------|-------------|-----------|
| Flame Bite | Fire | Fire | No change |
| Fire Blast | Fire | Fire | No change |
| Ember Shield | Fire | Fire | No change |
| Heat Wave | Fire | Fire | No change |
| Molten Fury | Fire | Fire | No change |
| Flame Dash | Fire | Fire | No change |

### Old Water Skills -> Water / Ice

| Skill | Old Element | New Element | Rationale |
|-------|-----------|-------------|-----------|
| Aqua Jet | Water | Water | No change |
| Healing Mist | Water | Water | No change |
| Tidal Wave | Water | Water | No change |
| Bubble Armor | Water | Water | No change |
| Hydro Cannon | Water | Water | No change |

### Old Wind Skills -> Wind (unchanged)

| Skill | Old Element | New Element | Rationale |
|-------|-----------|-------------|-----------|
| Gust Slash | Wind | Wind | No change |
| Tailwind Boost | Wind | Wind | No change |
| Sonic Screech | Wind | Wind | No change |
| Cyclone | Wind | Wind | No change |

### Old Neutral Skills -> Dark / Light

| Skill | Old Element | New Element | Rationale |
|-------|-----------|-------------|-----------|
| Shadow Bolt | Neutral | Dark | Shadow = dark |
| Confuse Dust | Neutral | Dark | Disorienting = dark |
| Prismatic Beam | Neutral | Light | Prismatic light |
| Aura Pulse | Neutral | Light | Healing aura = light |
| Life Drain | Neutral | Dark | Life drain = dark |

**Note**: No skills for Electric or Ice in MVP. New skills can be added in a future phase, or existing monsters with Electric/Ice typing will rely on STAB-less coverage moves for now.

---

## Tasks

### Phase 1: Core Type System (models + damage calc)

**Goal**: Update the Element enum, effectiveness matrix, damage calculation, and dual-type support at the model level. All existing tests must be updated to pass with new elements.

- [x] **Task 1.1** | Update `Element` enum in `models.py` -- replace 5 values with 10 new ones (WATER, FIRE, GRASS, ELECTRIC, WIND, GROUND, ROCK, DARK, LIGHT, ICE). Remove EARTH and NEUTRAL.
- [x] **Task 1.2** | Add dual-typing support to `MonsterSpecies` -- add `types: tuple[Element, Element | None]` field. Keep `element` as a computed property returning `types[0]` for backward compatibility during transition.
- [x] **Task 1.3** | Update `Monster` model -- ensure `effective_stats()`, `max_hp()`, and other methods work with dual-typed species. No stat changes needed.
- [x] **Task 1.4** | Create full 10x10 effectiveness matrix in `damage_calc.py` -- replace `ELEMENT_CHART` dict with the matrix defined above. Include the Ground immunity to Electric (0.0).
- [x] **Task 1.5** | Update `get_element_multiplier()` to accept optional second defender type -- signature becomes `get_element_multiplier(attack_element, defender_types)`. For dual-typed defenders, multiply both matchups.
- [x] **Task 1.6** | Update `calculate_damage()` -- pass both defender types to `get_element_multiplier()`. Update STAB to grant 1.5x if skill element matches EITHER of the attacker's types.
- [x] **Task 1.7** | Write comprehensive tests for type effectiveness -- test dual-type multiplication (4x, 1x, 0x edge cases), test STAB with dual-typed attackers, immunity tests. All 1079 tests passing.

**Dependencies**: None. This is the foundation.

**Success Criteria**: `Element` enum has 10 values. `MonsterSpecies` supports 1-2 types. Damage calc handles dual-type defenders and dual-type STAB. All new matchup tests pass.

**Files Changed**:
- `src/elements_rpg/monsters/models.py`
- `src/elements_rpg/combat/damage_calc.py`
- `src/elements_rpg/combat/tests/test_damage_calc.py`
- `src/elements_rpg/monsters/tests/test_models.py`

---

### Phase 2: Content Update (bestiary + skills)

**Goal**: Reassign all 12 monsters and 28 skills to the new element system. Some monsters gain dual types.

- [x] **Task 2.1** | Update all 12 monster species in `bestiary.py` -- change `element=` to `types=` per the monster redesign table above. 6 single-typed, 6 dual-typed.
- [x] **Task 2.2** | Update Earth skills in `skill_catalog.py` -- reassign to Grass, Rock, or Ground per the skill reassignment table.
- [x] **Task 2.3** | Update Neutral skills in `skill_catalog_extended.py` -- reassign to Dark or Light per the skill reassignment table.
- [x] **Task 2.4** | Update Wind and remaining skill categorization comments/headers in both catalog files.
- [x] **Task 2.5** | Verify all monsters' `learnable_skill_ids` still make sense -- ensure dual-typed monsters have skill coverage for at least one of their types (STAB). Adjust learnable lists if needed.
- [x] **Task 2.6** | Update `economy/areas.py` if any element references exist (likely no change, but verify). Verified: no element references.
- [x] **Task 2.7** | Write/update tests -- `test_bestiary.py` (verify all 12 monsters have valid types from new enum), `test_skill_catalog.py` (verify all 28 skills have valid elements). Add tests asserting specific type assignments match the plan.

**Dependencies**: Phase 1 complete (new Element enum and dual-type MonsterSpecies exist).

**Success Criteria**: All 12 monsters have correct new types (6 dual-typed). All 28 skills have correct new elements. No skill references an element that doesn't exist. All bestiary and skill catalog tests pass.

**Files Changed**:
- `src/elements_rpg/monsters/bestiary.py`
- `src/elements_rpg/monsters/skill_catalog.py`
- `src/elements_rpg/monsters/skill_catalog_extended.py`
- `src/elements_rpg/monsters/tests/test_bestiary.py`
- `src/elements_rpg/monsters/tests/test_skill_catalog.py`
- `src/elements_rpg/economy/areas.py` (verify only)

---

### Phase 3: Save/Load Compatibility + API Integration

**Goal**: Ensure old saves (v1) with old elements can be loaded and migrated. Update API responses to expose dual typing.

- [x] **Task 3.1** | Bump `SAVE_FORMAT_VERSION` to 2 in `save_load.py`.
- [x] **Task 3.2** | Add v1 -> v2 migration logic in `save_load.py` -- when loading a v1 save, map old element values: `earth` -> `grass` (default), `neutral` -> `dark` (default). Handles both old `element` field and `types` field with old values.
- [x] **Task 3.3** | Update `deserialize_save()` and `load_from_dict()` to detect version and apply migration before validation.
- [x] **Task 3.4** | Update `monster_service.py` -- `_enrich_monster_row` now exposes `types` as a list (e.g., `["fire", "ground"]`) alongside backward-compat `element` field.
- [x] **Task 3.5** | Update `db/converters.py` if it references element fields. Verified: no element field references, stores species_id only.
- [x] **Task 3.6** | Update `combat_service.py` if any element-specific logic exists. Verified: no element-specific logic, delegates to CombatManager.
- [x] **Task 3.7** | Write save/load migration tests -- 12 new tests covering v1 migration (earth->grass, neutral->dark, fire/water/wind unchanged, multiple monsters, empty saves, full round-trip via deserialize_save and load_from_dict, no double-migration of v2 saves, types field remapping).

**Dependencies**: Phase 2 complete (all content updated to new elements).

**Success Criteria**: Old v1 saves load successfully with correct element migration. API responses expose `types` array instead of single `element`. Save roundtrip works. No data loss on migration.

**Files Changed**:
- `src/elements_rpg/save_load.py`
- `src/elements_rpg/services/monster_service.py`
- `src/elements_rpg/db/converters.py`
- `src/elements_rpg/tests/test_save_load.py`
- `src/elements_rpg/api/tests/test_monsters.py`

---

### Phase 4: Full Test Suite Repair + E2E Validation

**Goal**: Fix all remaining broken tests across the entire codebase. Run E2E combat tests with dual-typed monsters.

- [ ] **Task 4.1** | Fix all failing tests that reference old Element values (EARTH, NEUTRAL) -- grep for `Element.EARTH`, `Element.NEUTRAL`, `"earth"`, `"neutral"` across all test files and update.
- [ ] **Task 4.2** | Update `combat/tests/test_manager.py` -- ensure combat tests use new elements and test dual-type combat scenarios.
- [ ] **Task 4.3** | Update `combat/tests/test_strategy.py` -- fix any element-dependent strategy tests.
- [ ] **Task 4.4** | Update API tests (`test_combat.py`, `test_e2e.py`, `test_taming.py`, `test_saves.py`) -- fix element references in test fixtures and assertions.
- [ ] **Task 4.5** | Update `services/tests/test_combat_service.py` -- fix service-level combat tests.
- [ ] **Task 4.6** | Create E2E combat test with dual-typed monsters -- Magma Wyrm (Fire/Ground) vs Aqua Serpent (Water/Ice), verify 4x multiplier Water -> Fire/Ground, verify STAB for dual-typed attacker.
- [ ] **Task 4.7** | Run full test suite (`uv run pytest`). Target: all 1068+ tests passing, zero failures. Run `uv run ruff check .` and `uv run ruff format --check .` -- zero issues.

**Dependencies**: Phase 3 complete (all production code updated).

**Success Criteria**: Full test suite passes (1068+ tests). Ruff lint clean. Ruff format clean. E2E combat with dual types validated. No regressions.

**Files Changed**:
- All test files referencing Element values (~20+ files)
- `src/elements_rpg/combat/tests/test_manager.py`
- `src/elements_rpg/combat/tests/test_damage_calc.py`
- `src/elements_rpg/api/tests/test_e2e.py`
- Various other test files

---

## Blockers

| Blocker | Phase | Impact | Resolution |
|---------|-------|--------|------------|
| None currently identified | -- | -- | -- |

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Replace `element` field with `types` tuple | Dual typing requires 1-2 elements per monster. A tuple of `(Element, Element \| None)` is the simplest representation. Keep `element` as backward-compat property. |
| Multiply dual-type matchups (not additive) | Follows Pokemon-style precedent: 2x * 2x = 4x for double weakness, 2x * 0.5x = 1x for offset. Creates meaningful strategic depth. |
| Only 1 immunity (Ground immune to Electric) | Immunities are powerful. Starting with just 1 keeps things balanced while adding strategic interest. More can be added later. |
| Map old elements in save migration, not per-field | Monsters reference species by ID, so migrating means looking up the new bestiary definition rather than mapping element values per-monster. Saves store species_id, and the species definition (in code) already has the correct new types. |
| No new Electric/Ice skills in this phase | Keep scope focused on the type system redesign. Electric/Ice typed monsters can use coverage moves. New skills can be added in a follow-up phase. |
| Dark/Light are symmetric | Each super effective against the other, each resists itself. Simple and intuitive for players. |

---

## Progress Log

| Date | Phase | Tasks Completed | Notes |
|------|-------|-----------------|-------|
| 2026-03-05 | -- | Plan created | 4 phases, 28 tasks, 10 elements, dual typing, full effectiveness matrix |
| 2026-03-05 | Phase 1 | Tasks 1.1-1.7 complete | 10 elements, dual typing, effectiveness matrix, damage calc updated. Also updated bestiary (12 monsters) and skill catalogs (28 skills) to new elements. 1079 tests passing. |
| 2026-03-05 | Phase 2 | Tasks 2.1-2.7 complete | Content verified: all 12 monsters use new elements (6 dual-typed), all 28 skills use valid elements, no EARTH/NEUTRAL references remain. Areas have no element refs. |
| 2026-03-05 | Phase 3 | Tasks 3.1-3.7 complete | Save version bumped to 2. V1->V2 migration (earth->grass, neutral->dark). API exposes `types` array. 12 new migration tests. 1091 tests passing. |

---

## Notes

- The `element` field on `MonsterSpecies` is used in ~86 files. The backward-compat property on MonsterSpecies will minimize churn -- most code accessing `species.element` will continue to work (returns primary type).
- The damage_calc.py change is the most critical -- it's the only place where type effectiveness is evaluated at runtime.
- STAB (Same Type Attack Bonus) must check BOTH types of the attacker for dual-typed monsters.
- The save migration is simple because monsters in saves reference species by ID. When the game loads, it looks up the species from the bestiary (which will have the new types). The only risk is if old saves stored the element value directly -- `GameSaveData.monsters` stores full `Monster` objects with embedded `MonsterSpecies`, so the migration must update the embedded species data.
- Electric and Ice have no dedicated skills yet. This is intentional scope limitation. Dual-typed monsters like Meadow Fox (Wind/Electric) get STAB on Wind moves but not Electric. Future work can add Electric/Ice skills.
