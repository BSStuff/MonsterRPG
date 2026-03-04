# Monster Survival RPG -- Product Requirements Document (PRD)

## 1. Overview

### Vision

Develop a hybrid Active + Idle Monster Survival RPG built in Unity (Web
first, then mobile). The game combines: - Auto-combat survival
gameplay - Monster collection and taming - Persistent skill
progression - Strategy-based AI customization - Life skills and resource
economy - Convenience-based monetization (no forced ads)

### Platform Strategy

-   Phase 1: Web (Unity WebGL)
-   Phase 2: iOS & Android

### Business Model

Free-to-play with: - Optional reward ads - Subscription tiers - Battle
pass (Phase 2) - Cosmetic store - Convenience purchases

------------------------------------------------------------------------

## 2. Core Gameplay Loop

1.  Select Team (up to 6 monsters)
2.  Choose Area
3.  Active Clear (improve efficiency)
4.  Gather Materials
5.  Attempt Taming
6.  Craft / Train via Action Queue
7.  Assign Idle Farming
8.  Log Off → Offline Gains
9.  Return → Upgrade → Repeat

------------------------------------------------------------------------

## 3. Core Systems

### 3.1 Combat System

-   Player manually moves character
-   Monsters auto-follow and auto-attack
-   Each monster has:
    -   Level (permanent)
    -   Bond Level
    -   4 Active Skills
    -   Passive Trait
    -   Stats:
        -   HP
        -   Attack
        -   Defense
        -   Special Attack
        -   Special Defense
        -   Speed
    -   Strategy Profile
    -   Taming Difficulty

### 3.2 Skill System

Each monster has 4 equipped skills.

Skill Progression: - Levels via usage - Improves: - Damage scaling -
Cooldown reduction - AoE size - Buff duration - Proc chance

Milestone upgrades at defined levels (e.g., 10, 25, 50).

------------------------------------------------------------------------

## 4. Strategy AI System

Monsters operate via selectable strategies.

Base Strategies: - Attack Nearest - Follow Player - Defensive (no
chase) - Aggressive (long chase) - Heal Lowest HP

### Strategy Mastery

Each strategy has proficiency levels. - Low level = imperfect
execution - High level = optimized targeting

Strategy training occurs via: - Combat usage - Action Queue training

------------------------------------------------------------------------

## 5. Idle System

Each area tracks:

-   Fastest Clear Time
-   Resource Yield
-   Best Resource Rate Per Minute (BRPM)

Idle Gains Formula:

Idle Rate = 85% of Best Recorded BRPM

Idle gains: - Cannot exceed best active performance - Improve when
player clears faster

Offline cap: - Base: 8 hours - Expandable via upgrades/subscription

------------------------------------------------------------------------

## 6. Areas & Taming

Each area includes: - Exclusive monsters - Exclusive materials -
Difficulty scaling - Taming base rate

### Taming Formula (Conceptual)

Final Tame Chance = Base Rate × (Food Bonus + Player Taming Skill +
Monster Status Modifier)

Soft pity system implemented after repeated failures.

------------------------------------------------------------------------

## 7. Life Skills (MVP Scope)

Phase 1: - Mining - Cooking - Strategy Training

Future: - Fishing - Foraging - Tailoring - Brewing - Woodcutting -
Enhancing

All life skills level permanently.

------------------------------------------------------------------------

## 8. Unified Action Queue

Single queue per player.

Queue supports: - Crafting - Cooking - Strategy Training - Skill
Training

Base Slots: 2\
Upgradeable: up to 6--8\
Subscription Bonus: +1 slot

------------------------------------------------------------------------

## 9. Team System

Max Monsters per Team: 6

Suggested Composition: - 1 Tank - 1 Off-Tank - 2 DPS - 1 Main Support -
1 Flex Support

Multiple Teams unlockable via upgrades.

------------------------------------------------------------------------

## 10. Monetization Design

### 10.1 Reward Ads (Optional Only)

-   Revive
-   +25% idle gains (temporary)
-   Bonus taming attempt
-   Temporary resource boost

No forced pop-ups.

### 10.2 Premium Currency (Gems)

Used for: - Team slot expansion - Action queue expansion - Offline cap
expansion - Inventory expansion - Cosmetic purchases - Convenience
boosts

No direct stat purchases.

### 10.3 Subscription Tiers

30-Day / 90-Day / 1-Year options.

Benefits: - Ad removal - +10% idle cap - +1 action slot - Daily gems -
Exclusive cosmetics

Power advantage capped at minor convenience levels.

### 10.4 Battle Pass (Phase 2)

-   60-day season
-   Free + Premium tracks
-   Cosmetics
-   Shards
-   Premium currency

------------------------------------------------------------------------

## 11. MVP Scope (Web POC)

Included: - 2 Areas - 12 Monsters - 3 Life Skills - 1 Action Queue - 1
Team - Skill leveling - Basic strategy leveling - Idle system - Optional
reward ads

Excluded (Phase 2): - PvP - Guilds - Global chat - Community buffs -
Battle pass

------------------------------------------------------------------------

## 12. Technical Architecture (Unity)

Engine: Unity\
Language: C#\
Target: WebGL → Mobile

Core Systems Required: - Entity Component System (lightweight) - Combat
Manager - AI Behavior Module - Idle Efficiency Tracker - Economy
Manager - Save/Load System (cloud-ready) - Modular Live-Ops system
(future)

------------------------------------------------------------------------

## 13. Long-Term Expansion

Phase 2: - Guilds - Global chat - Cosmetics expansion - Battle pass -
Community buffs

Phase 3: - Asynchronous PvP - Ranked seasons

Phase 4: - Real-time PvP

------------------------------------------------------------------------

## 14. Success Metrics

-   D1 Retention \> 40%
-   D7 Retention \> 15%
-   Avg Session Length: 10--15 min
-   Subscription Conversion Target: 3--5%
-   ARPDAU growth via cosmetics + convenience

------------------------------------------------------------------------

End of Document
