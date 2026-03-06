"""Tests for the save/load system — serialization, round-trips, and edge cases."""

import json

from elements_rpg.economy.action_queue import ActionQueue, ActionType, QueuedAction
from elements_rpg.economy.crafting import Inventory
from elements_rpg.economy.life_skills import LifeSkill, LifeSkillType
from elements_rpg.economy.manager import EconomyManager
from elements_rpg.economy.reward_ads import AdRewardType, AdWatchRecord, RewardAdTracker
from elements_rpg.economy.subscription import (
    PlayerSubscription,
    SubscriptionBenefits,
    SubscriptionPlan,
    SubscriptionTier,
)
from elements_rpg.idle.tracker import IdleTracker
from elements_rpg.monsters.models import Element, Monster, MonsterSpecies, Rarity, StatBlock
from elements_rpg.monsters.taming import TamingTracker
from elements_rpg.monsters.team import Team, TeamSlot
from elements_rpg.player import Player
from elements_rpg.save_load import (
    SAVE_FORMAT_VERSION,
    GameSaveData,
    _migrate_v1_to_v2,
    create_new_save,
    deserialize_save,
    load_from_dict,
    save_to_dict,
    serialize_save,
    validate_save_version,
)

# ==========================================
# Test fixtures / helpers
# ==========================================


def _make_species(**overrides: object) -> MonsterSpecies:
    """Create a MonsterSpecies with sensible defaults."""
    defaults: dict[str, object] = {
        "species_id": "sp_fire_wolf",
        "name": "Fire Wolf",
        "types": (Element.FIRE, None),
        "rarity": Rarity.COMMON,
        "base_stats": StatBlock(
            hp=100, attack=20, defense=15, speed=18, magic_attack=10, magic_defense=12
        ),
        "passive_trait": "Flame Body",
        "passive_description": "Burns attackers on contact",
        "learnable_skill_ids": ["sk_fireball", "sk_tackle"],
    }
    defaults.update(overrides)
    return MonsterSpecies(**defaults)


def _make_monster(**overrides: object) -> Monster:
    """Create a Monster with sensible defaults."""
    species = _make_species()
    defaults: dict[str, object] = {
        "monster_id": "mon_001",
        "species": species,
        "current_hp": species.base_stats.hp,
    }
    defaults.update(overrides)
    return Monster(**defaults)


def _make_player(**overrides: object) -> Player:
    """Create a Player with sensible defaults."""
    defaults: dict[str, object] = {
        "player_id": "player_001",
        "username": "TestHero",
    }
    defaults.update(overrides)
    return Player(**defaults)


def _make_save(**overrides: object) -> GameSaveData:
    """Create a GameSaveData with sensible defaults."""
    defaults: dict[str, object] = {
        "player": _make_player(),
    }
    defaults.update(overrides)
    return GameSaveData(**defaults)


# ==========================================
# GameSaveData construction tests
# ==========================================


class TestGameSaveDataConstruction:
    """Tests for GameSaveData model construction."""

    def test_minimal_construction(self) -> None:
        """GameSaveData with just a player should work."""
        save = _make_save()
        assert save.player.player_id == "player_001"

    def test_default_values_populated(self) -> None:
        """All default fields should be populated correctly."""
        save = _make_save()
        assert save.monsters == []
        assert save.teams == []
        assert save.inventory.items == {}
        assert save.economy.gold == 0
        assert save.economy.gems == 0
        assert save.idle_tracker.best_clear_times == {}
        assert save.taming_tracker.attempts_per_species == {}
        assert save.action_queue.actions == []
        assert save.life_skills == []
        assert save.subscription.active_plan is None
        assert save.ad_tracker.watches_today == {}
        assert save.premium_purchases == {}
        assert save.timestamp == 0

    def test_version_defaults_to_save_format_version(self) -> None:
        """Version field should default to SAVE_FORMAT_VERSION."""
        save = _make_save()
        assert save.version == SAVE_FORMAT_VERSION
        assert save.version == 2

    def test_custom_version(self) -> None:
        """Version can be set explicitly."""
        save = _make_save(version=42)
        assert save.version == 42


# ==========================================
# Serialization round-trip tests
# ==========================================


class TestSerializationRoundTrip:
    """Tests for serialize/deserialize round-trips."""

    def test_serialize_produces_valid_json(self) -> None:
        """serialize_save should produce a valid JSON string."""
        save = _make_save()
        json_str = serialize_save(save)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "player" in parsed
        assert "version" in parsed

    def test_deserialize_restores_exact_data(self) -> None:
        """deserialize_save should restore the exact same data."""
        save = _make_save()
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.player.player_id == save.player.player_id
        assert restored.player.username == save.player.username
        assert restored.version == save.version

    def test_full_round_trip_compare(self) -> None:
        """Full round-trip: create -> serialize -> deserialize -> compare."""
        save = _make_save(timestamp=1234567890.0)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        # Compare full model dumps for equality
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_monsters(self) -> None:
        """Round-trip with monsters in the save."""
        monster1 = _make_monster(monster_id="mon_001", level=5, bond_level=20)
        monster2 = _make_monster(
            monster_id="mon_002",
            species=_make_species(
                species_id="sp_water_serpent",
                name="Water Serpent",
                types=(Element.WATER, None),
                rarity=Rarity.RARE,
            ),
            current_hp=80,
            level=10,
        )
        save = _make_save(monsters=[monster1, monster2])
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert len(restored.monsters) == 2
        assert restored.monsters[0].monster_id == "mon_001"
        assert restored.monsters[0].level == 5
        assert restored.monsters[0].bond_level == 20
        assert restored.monsters[1].monster_id == "mon_002"
        assert restored.monsters[1].species.element == Element.WATER
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_teams(self) -> None:
        """Round-trip with teams in the save."""
        team = Team(
            team_id="team_1",
            name="Alpha Squad",
            slots=[
                TeamSlot(monster_id="mon_001", position=0),
                TeamSlot(monster_id="mon_002", position=1),
            ],
        )
        save = _make_save(teams=[team])
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert len(restored.teams) == 1
        assert restored.teams[0].team_id == "team_1"
        assert restored.teams[0].name == "Alpha Squad"
        assert len(restored.teams[0].slots) == 2
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_inventory(self) -> None:
        """Round-trip with populated inventory."""
        inv = Inventory()
        inv.add_material("iron_ore", 50)
        inv.add_material("wood", 100)
        save = _make_save(inventory=inv)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.inventory.get_quantity("iron_ore") == 50
        assert restored.inventory.get_quantity("wood") == 100
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_economy(self) -> None:
        """Round-trip with economy data including transactions."""
        econ = EconomyManager()
        econ.earn_gold(500, "quest_reward")
        econ.earn_gems(100, "purchase")
        save = _make_save(economy=econ)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.economy.gold == 500
        assert restored.economy.gems == 100
        assert len(restored.economy.transaction_log) == 2
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_life_skills(self) -> None:
        """Round-trip with life skills data."""
        mining = LifeSkill(skill_type=LifeSkillType.MINING, level=15, experience=200)
        cooking = LifeSkill(skill_type=LifeSkillType.COOKING, level=8, experience=50)
        save = _make_save(life_skills=[mining, cooking])
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert len(restored.life_skills) == 2
        assert restored.life_skills[0].skill_type == LifeSkillType.MINING
        assert restored.life_skills[0].level == 15
        assert restored.life_skills[1].skill_type == LifeSkillType.COOKING
        assert restored.life_skills[1].level == 8
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_subscription(self) -> None:
        """Round-trip with active subscription."""
        plan = SubscriptionPlan(
            plan_id="sub_monthly",
            tier=SubscriptionTier.MONTHLY,
            name="Monthly Pass",
            duration_days=30,
            price_usd=4.99,
            benefits=SubscriptionBenefits(),
        )
        sub = PlayerSubscription(
            active_plan=plan,
            start_timestamp=1000.0,
            end_timestamp=3592000.0,
            auto_renew=True,
        )
        save = _make_save(subscription=sub)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.subscription.is_active(current_time=1500.0) is True
        assert restored.subscription.auto_renew is True
        assert restored.subscription.active_plan is not None
        assert restored.subscription.active_plan.tier == SubscriptionTier.MONTHLY
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_ad_tracker(self) -> None:
        """Round-trip with ad tracker data."""
        tracker = RewardAdTracker(
            watches_today={"revive": 2, "idle_boost": 1},
            last_watch_time={"revive": 50000.0},
            watch_history=[
                AdWatchRecord(
                    reward_type=AdRewardType.REVIVE,
                    timestamp=50000.0,
                    bonus_applied=0.5,
                ),
            ],
        )
        save = _make_save(ad_tracker=tracker)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.ad_tracker.watches_today["revive"] == 2
        assert len(restored.ad_tracker.watch_history) == 1
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_idle_tracker(self) -> None:
        """Round-trip with idle tracker records."""
        idle = IdleTracker(
            best_clear_times={"area_forest": 45.0, "area_cave": 90.0},
            best_monsters_per_clear={"area_forest": 5, "area_cave": 8},
        )
        save = _make_save(idle_tracker=idle)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.idle_tracker.best_clear_times["area_forest"] == 45.0
        assert restored.idle_tracker.best_monsters_per_clear["area_cave"] == 8
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_taming_tracker(self) -> None:
        """Round-trip with taming tracker data."""
        taming = TamingTracker(attempts_per_species={"sp_fire_wolf": 12, "sp_water_serpent": 3})
        save = _make_save(taming_tracker=taming)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.taming_tracker.get_attempts("sp_fire_wolf") == 12
        assert restored.taming_tracker.get_attempts("sp_water_serpent") == 3
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_premium_purchases(self) -> None:
        """Round-trip with premium purchase counts."""
        save = _make_save(premium_purchases={"upgrade_queue_slot": 3, "upgrade_offline_cap": 1})
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.premium_purchases["upgrade_queue_slot"] == 3
        assert restored.premium_purchases["upgrade_offline_cap"] == 1
        assert save.model_dump() == restored.model_dump()

    def test_round_trip_with_action_queue(self) -> None:
        """Round-trip with action queue containing actions."""
        action = QueuedAction(
            action_id="act_001",
            action_type=ActionType.MINE,
            name="Mine Iron",
            duration_seconds=60.0,
            elapsed_seconds=30.0,
        )
        queue = ActionQueue()
        queue.add_action(action)
        save = _make_save(action_queue=queue)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert len(restored.action_queue.actions) == 1
        assert restored.action_queue.actions[0].action_id == "act_001"
        assert restored.action_queue.actions[0].elapsed_seconds == 30.0
        assert save.model_dump() == restored.model_dump()


# ==========================================
# Dict round-trip tests
# ==========================================


class TestDictRoundTrip:
    """Tests for save_to_dict / load_from_dict."""

    def test_dict_round_trip(self) -> None:
        """save_to_dict -> load_from_dict should preserve data."""
        save = _make_save(timestamp=9999.0)
        data = save_to_dict(save)
        restored = load_from_dict(data)
        assert save.model_dump() == restored.model_dump()

    def test_dict_output_has_expected_keys(self) -> None:
        """save_to_dict output should have all top-level keys."""
        save = _make_save()
        data = save_to_dict(save)
        expected_keys = {
            "version",
            "player",
            "monsters",
            "teams",
            "inventory",
            "economy",
            "idle_tracker",
            "taming_tracker",
            "action_queue",
            "life_skills",
            "subscription",
            "ad_tracker",
            "premium_purchases",
            "timestamp",
        }
        assert set(data.keys()) == expected_keys


# ==========================================
# create_new_save tests
# ==========================================


class TestCreateNewSave:
    """Tests for create_new_save."""

    def test_creates_valid_save(self) -> None:
        """create_new_save should produce a valid GameSaveData."""
        save = create_new_save("player_abc", "NewPlayer")
        assert isinstance(save, GameSaveData)
        assert save.version == SAVE_FORMAT_VERSION

    def test_player_id_and_username_set(self) -> None:
        """Player ID and username should be set correctly."""
        save = create_new_save("player_xyz", "HeroName")
        assert save.player.player_id == "player_xyz"
        assert save.player.username == "HeroName"

    def test_three_life_skills_initialized(self) -> None:
        """Should initialize all 3 life skills at level 1."""
        save = create_new_save("p1", "User1")
        assert len(save.life_skills) == 3
        skill_types = {ls.skill_type for ls in save.life_skills}
        assert skill_types == {
            LifeSkillType.MINING,
            LifeSkillType.COOKING,
            LifeSkillType.STRATEGY_TRAINING,
        }
        for ls in save.life_skills:
            assert ls.level == 1
            assert ls.experience == 0

    def test_default_empty_collections(self) -> None:
        """New save should have empty monster/team/inventory/etc."""
        save = create_new_save("p1", "User1")
        assert save.monsters == []
        assert save.teams == []
        assert save.inventory.items == {}
        assert save.economy.gold == 0
        assert save.premium_purchases == {}
        assert save.action_queue.actions == []


# ==========================================
# validate_save_version tests
# ==========================================


class TestValidateSaveVersion:
    """Tests for validate_save_version."""

    def test_returns_correct_version(self) -> None:
        """Should return the version from the JSON."""
        save = _make_save()
        json_str = serialize_save(save)
        assert validate_save_version(json_str) == SAVE_FORMAT_VERSION

    def test_returns_zero_for_missing_version(self) -> None:
        """Should return 0 if version key is missing."""
        json_str = json.dumps({"player": {"player_id": "p1", "username": "X"}})
        assert validate_save_version(json_str) == 0

    def test_returns_custom_version(self) -> None:
        """Should return whatever version is in the JSON."""
        json_str = json.dumps({"version": 99})
        assert validate_save_version(json_str) == 99


# ==========================================
# Edge case tests
# ==========================================


class TestEdgeCases:
    """Edge case and forward compatibility tests."""

    def test_save_with_empty_monster_list(self) -> None:
        """Save with explicitly empty monster list should round-trip."""
        save = _make_save(monsters=[])
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.monsters == []

    def test_save_with_populated_inventory(self) -> None:
        """Save with inventory items should round-trip correctly."""
        inv = Inventory()
        inv.add_material("diamond", 5)
        inv.add_material("coal", 999)
        save = _make_save(inventory=inv)
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.inventory.get_quantity("diamond") == 5
        assert restored.inventory.get_quantity("coal") == 999

    def test_unknown_fields_ignored_on_deserialization(self) -> None:
        """Unknown fields in JSON should be ignored (forward compat)."""
        save = _make_save()
        json_str = serialize_save(save)
        data = json.loads(json_str)
        data["future_field"] = "some_value"
        data["another_unknown"] = [1, 2, 3]
        modified_json = json.dumps(data)
        # Pydantic ignores extra fields by default
        restored = deserialize_save(modified_json)
        assert restored.player.player_id == "player_001"
        assert not hasattr(restored, "future_field")

    def test_full_save_round_trip_with_all_systems(self) -> None:
        """Comprehensive round-trip with data in every subsystem."""
        monster = _make_monster(level=25, bond_level=50, experience=1000)
        team = Team(
            team_id="t1",
            slots=[TeamSlot(monster_id="mon_001", position=0)],
        )
        inv = Inventory()
        inv.add_material("gold_ore", 42)
        econ = EconomyManager()
        econ.earn_gold(1000, "farming")
        idle = IdleTracker(
            best_clear_times={"area_1": 30.0},
            best_monsters_per_clear={"area_1": 4},
        )
        taming = TamingTracker(attempts_per_species={"sp_fire_wolf": 7})
        mining = LifeSkill(skill_type=LifeSkillType.MINING, level=20, experience=500)
        sub = PlayerSubscription(
            active_plan=SubscriptionPlan(
                plan_id="sub_monthly",
                tier=SubscriptionTier.MONTHLY,
                name="Monthly Pass",
                duration_days=30,
                price_usd=4.99,
                benefits=SubscriptionBenefits(),
            ),
            start_timestamp=1000.0,
            end_timestamp=2592000.0,
            auto_renew=True,
        )
        ad_tracker = RewardAdTracker(watches_today={"revive": 1})

        save = GameSaveData(
            player=_make_player(level=15),
            monsters=[monster],
            teams=[team],
            inventory=inv,
            economy=econ,
            idle_tracker=idle,
            taming_tracker=taming,
            life_skills=[mining],
            subscription=sub,
            ad_tracker=ad_tracker,
            premium_purchases={"upgrade_queue_slot": 2},
            timestamp=1709568000.0,
        )

        # JSON round-trip
        json_str = serialize_save(save)
        restored_json = deserialize_save(json_str)
        assert save.model_dump() == restored_json.model_dump()

        # Dict round-trip
        data = save_to_dict(save)
        restored_dict = load_from_dict(data)
        assert save.model_dump() == restored_dict.model_dump()


# ==========================================
# V1 -> V2 migration tests
# ==========================================


def _make_v1_save_dict(**overrides: object) -> dict:
    """Create a raw v1-format save dict with old element values."""
    base: dict = {
        "version": 1,
        "player": {"player_id": "player_001", "username": "TestHero"},
        "monsters": [],
        "teams": [],
        "inventory": {"items": {}},
        "economy": {"gold": 0, "gems": 0, "transaction_log": []},
        "idle_tracker": {"best_clear_times": {}, "best_monsters_per_clear": {}},
        "taming_tracker": {"attempts_per_species": {}},
        "action_queue": {"actions": [], "max_slots": 2},
        "life_skills": [],
        "subscription": {
            "active_plan": None,
            "start_timestamp": 0,
            "end_timestamp": 0,
            "auto_renew": False,
        },
        "ad_tracker": {
            "watches_today": {},
            "last_watch_time": {},
            "watch_history": [],
        },
        "premium_purchases": {},
        "timestamp": 0,
    }
    base.update(overrides)
    return base


def _make_v1_monster_dict(
    monster_id: str = "mon_001",
    species_id: str = "sp_earth_golem",
    name: str = "Earth Golem",
    element: str = "earth",
    level: int = 5,
) -> dict:
    """Create a v1-format monster dict with old single `element` field."""
    return {
        "monster_id": monster_id,
        "species": {
            "species_id": species_id,
            "name": name,
            "element": element,
            "rarity": "common",
            "base_stats": {
                "hp": 100,
                "attack": 20,
                "defense": 15,
                "speed": 18,
                "magic_attack": 10,
                "magic_defense": 12,
            },
            "passive_trait": "Sturdy",
            "passive_description": "Resists knockback",
            "learnable_skill_ids": ["sk_tackle"],
        },
        "level": level,
        "experience": 0,
        "bond_level": 0,
        "equipped_skill_ids": [],
        "current_hp": 100,
        "is_fainted": False,
    }


class TestV1ToV2Migration:
    """Tests for v1 -> v2 save migration."""

    def test_migrate_bumps_version_to_2(self) -> None:
        """Migration should set version to 2."""
        v1_data = _make_v1_save_dict()
        result = _migrate_v1_to_v2(v1_data)
        assert result["version"] == 2

    def test_migrate_earth_to_grass(self) -> None:
        """earth element should migrate to grass."""
        monster = _make_v1_monster_dict(element="earth")
        v1_data = _make_v1_save_dict(monsters=[monster])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert "types" in species
        assert species["types"][0] == "grass"
        assert species["types"][1] is None
        assert "element" not in species

    def test_migrate_neutral_to_dark(self) -> None:
        """neutral element should migrate to dark."""
        monster = _make_v1_monster_dict(
            species_id="sp_shadow",
            name="Shadow",
            element="neutral",
        )
        v1_data = _make_v1_save_dict(monsters=[monster])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert species["types"][0] == "dark"
        assert species["types"][1] is None

    def test_migrate_fire_stays_fire(self) -> None:
        """fire element should remain fire."""
        monster = _make_v1_monster_dict(element="fire")
        v1_data = _make_v1_save_dict(monsters=[monster])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert species["types"][0] == "fire"

    def test_migrate_water_stays_water(self) -> None:
        """water element should remain water."""
        monster = _make_v1_monster_dict(element="water")
        v1_data = _make_v1_save_dict(monsters=[monster])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert species["types"][0] == "water"

    def test_migrate_wind_stays_wind(self) -> None:
        """wind element should remain wind."""
        monster = _make_v1_monster_dict(element="wind")
        v1_data = _make_v1_save_dict(monsters=[monster])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert species["types"][0] == "wind"

    def test_migrate_multiple_monsters(self) -> None:
        """All monsters in the save should be migrated."""
        monsters = [
            _make_v1_monster_dict(monster_id="mon_001", element="earth", species_id="sp_1"),
            _make_v1_monster_dict(monster_id="mon_002", element="neutral", species_id="sp_2"),
            _make_v1_monster_dict(monster_id="mon_003", element="fire", species_id="sp_3"),
        ]
        v1_data = _make_v1_save_dict(monsters=monsters)
        result = _migrate_v1_to_v2(v1_data)
        assert result["monsters"][0]["species"]["types"][0] == "grass"
        assert result["monsters"][1]["species"]["types"][0] == "dark"
        assert result["monsters"][2]["species"]["types"][0] == "fire"

    def test_migrate_no_monsters(self) -> None:
        """Migration should handle saves with no monsters."""
        v1_data = _make_v1_save_dict(monsters=[])
        result = _migrate_v1_to_v2(v1_data)
        assert result["version"] == 2
        assert result["monsters"] == []

    def test_v1_save_loads_via_deserialize(self) -> None:
        """A v1 save JSON should load correctly through deserialize_save."""
        monster = _make_v1_monster_dict(element="earth")
        v1_data = _make_v1_save_dict(monsters=[monster])
        json_str = json.dumps(v1_data)
        restored = deserialize_save(json_str)
        assert restored.version == 2
        assert len(restored.monsters) == 1
        assert restored.monsters[0].species.primary_type == Element.GRASS
        assert restored.monsters[0].species.secondary_type is None

    def test_v1_save_loads_via_load_from_dict(self) -> None:
        """A v1 save dict should load correctly through load_from_dict."""
        monster = _make_v1_monster_dict(element="neutral")
        v1_data = _make_v1_save_dict(monsters=[monster])
        restored = load_from_dict(v1_data)
        assert restored.version == 2
        assert restored.monsters[0].species.primary_type == Element.DARK

    def test_v2_save_not_double_migrated(self) -> None:
        """A v2 save should not be re-migrated."""
        save = _make_save(
            monsters=[_make_monster()],
        )
        json_str = serialize_save(save)
        restored = deserialize_save(json_str)
        assert restored.version == 2
        assert restored.monsters[0].species.primary_type == Element.FIRE

    def test_migrate_preserves_existing_types_field(self) -> None:
        """If a v1 save somehow has types, remap old values in the tuple."""
        monster_dict = _make_v1_monster_dict()
        # Simulate having types with old element values
        monster_dict["species"].pop("element", None)
        monster_dict["species"]["types"] = ["earth", "neutral"]
        v1_data = _make_v1_save_dict(monsters=[monster_dict])
        result = _migrate_v1_to_v2(v1_data)
        species = result["monsters"][0]["species"]
        assert species["types"] == ["grass", "dark"]
