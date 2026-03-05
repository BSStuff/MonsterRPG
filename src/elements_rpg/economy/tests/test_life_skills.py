"""Tests for life skills system — Mining, Cooking, Strategy Training."""

import pytest
from pydantic import ValidationError

from elements_rpg.economy.life_skills import (
    LifeSkill,
    LifeSkillAction,
    LifeSkillType,
    ResourceYield,
    calculate_action_duration,
    calculate_resource_yield,
    life_skill_xp_for_level,
)

# ---------------------------------------------------------------------------
# LifeSkillType tests
# ---------------------------------------------------------------------------


class TestLifeSkillType:
    """Tests for the LifeSkillType enum."""

    def test_all_three_types_exist(self) -> None:
        assert len(LifeSkillType) == 3

    def test_mining_value(self) -> None:
        assert LifeSkillType.MINING == "mining"

    def test_cooking_value(self) -> None:
        assert LifeSkillType.COOKING == "cooking"

    def test_strategy_training_value(self) -> None:
        assert LifeSkillType.STRATEGY_TRAINING == "strategy_training"


# ---------------------------------------------------------------------------
# life_skill_xp_for_level tests
# ---------------------------------------------------------------------------


class TestLifeSkillXpForLevel:
    """Tests for the XP-per-level formula."""

    def test_level_1_returns_zero(self) -> None:
        assert life_skill_xp_for_level(1) == 0

    def test_level_0_returns_zero(self) -> None:
        assert life_skill_xp_for_level(0) == 0

    def test_level_2_returns_positive(self) -> None:
        result = life_skill_xp_for_level(2)
        assert result > 0
        assert result == int(75 * (2**1.4))

    def test_level_10_returns_positive(self) -> None:
        result = life_skill_xp_for_level(10)
        assert result == int(75 * (10**1.4))

    def test_monotonically_increasing(self) -> None:
        """XP requirements should increase with each level."""
        for lvl in range(2, 50):
            assert life_skill_xp_for_level(lvl + 1) > life_skill_xp_for_level(lvl)


# ---------------------------------------------------------------------------
# LifeSkill tests
# ---------------------------------------------------------------------------


class TestLifeSkill:
    """Tests for LifeSkill model and methods."""

    def test_construction_defaults(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        assert skill.level == 1
        assert skill.experience == 0
        assert skill.skill_type == LifeSkillType.MINING

    def test_construction_with_values(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.COOKING, level=10, experience=50)
        assert skill.level == 10
        assert skill.experience == 50

    def test_gain_experience_single_level(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        xp_needed = life_skill_xp_for_level(2)
        levels = skill.gain_experience(xp_needed)
        assert levels == [2]
        assert skill.level == 2
        assert skill.experience == 0

    def test_gain_experience_multi_level(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        # Give enough XP to jump several levels
        huge_xp = sum(life_skill_xp_for_level(lvl) for lvl in range(2, 6))
        levels = skill.gain_experience(huge_xp)
        assert levels == [2, 3, 4, 5]
        assert skill.level == 5

    def test_gain_experience_caps_at_99(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.COOKING, level=98)
        xp_needed = life_skill_xp_for_level(99)
        levels = skill.gain_experience(xp_needed + 999999)
        assert 99 in levels
        assert skill.level == 99

    def test_gain_experience_leftover_xp(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        xp_needed = life_skill_xp_for_level(2)
        skill.gain_experience(xp_needed + 25)
        assert skill.level == 2
        assert skill.experience == 25

    def test_gain_experience_raises_on_zero(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        with pytest.raises(ValueError, match="XP must be positive"):
            skill.gain_experience(0)

    def test_gain_experience_raises_on_negative(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        with pytest.raises(ValueError, match="XP must be positive"):
            skill.gain_experience(-10)

    def test_resource_bonus_level_1(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        assert skill.resource_bonus() == pytest.approx(1.0)

    def test_resource_bonus_level_50(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=50)
        assert skill.resource_bonus() == pytest.approx(1.49)

    def test_speed_bonus_level_1(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        assert skill.speed_bonus() == pytest.approx(1.0)

    def test_speed_bonus_level_50(self) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=50)
        assert skill.speed_bonus() == pytest.approx(0.755)

    def test_level_validation_rejects_zero(self) -> None:
        with pytest.raises(ValidationError):
            LifeSkill(skill_type=LifeSkillType.MINING, level=0)

    def test_level_validation_rejects_over_99(self) -> None:
        with pytest.raises(ValidationError):
            LifeSkill(skill_type=LifeSkillType.MINING, level=100)


# ---------------------------------------------------------------------------
# LifeSkillAction tests
# ---------------------------------------------------------------------------


class TestLifeSkillAction:
    """Tests for LifeSkillAction model."""

    def test_valid_construction(self) -> None:
        action = LifeSkillAction(
            action_id="mine_iron",
            name="Mine Iron Ore",
            skill_type=LifeSkillType.MINING,
            required_level=1,
            base_duration_seconds=10.0,
            xp_reward=15,
            resource_yields=[
                ResourceYield(
                    resource_id="iron_ore",
                    resource_name="Iron Ore",
                    quantity=3,
                ),
            ],
        )
        assert action.action_id == "mine_iron"
        assert action.xp_reward == 15
        assert len(action.resource_yields) == 1

    def test_validation_empty_action_id(self) -> None:
        with pytest.raises(ValidationError):
            LifeSkillAction(
                action_id="",
                name="Mine Iron Ore",
                skill_type=LifeSkillType.MINING,
                base_duration_seconds=10.0,
                xp_reward=15,
            )

    def test_validation_zero_duration(self) -> None:
        with pytest.raises(ValidationError):
            LifeSkillAction(
                action_id="mine_iron",
                name="Mine Iron Ore",
                skill_type=LifeSkillType.MINING,
                base_duration_seconds=0,
                xp_reward=15,
            )

    def test_validation_zero_xp(self) -> None:
        with pytest.raises(ValidationError):
            LifeSkillAction(
                action_id="mine_iron",
                name="Mine Iron Ore",
                skill_type=LifeSkillType.MINING,
                base_duration_seconds=10.0,
                xp_reward=0,
            )

    def test_life_skill_action_zero_material_raises(self) -> None:
        with pytest.raises(ValidationError, match="quantity must be >= 1"):
            LifeSkillAction(
                action_id="cook_steak",
                name="Cook Steak",
                skill_type=LifeSkillType.COOKING,
                base_duration_seconds=15.0,
                xp_reward=20,
                required_materials={"raw_meat": 0},
            )

    def test_required_materials(self) -> None:
        action = LifeSkillAction(
            action_id="cook_steak",
            name="Cook Steak",
            skill_type=LifeSkillType.COOKING,
            base_duration_seconds=15.0,
            xp_reward=20,
            required_materials={"raw_meat": 1, "salt": 1},
        )
        assert action.required_materials == {"raw_meat": 1, "salt": 1}


# ---------------------------------------------------------------------------
# calculate_action_duration tests
# ---------------------------------------------------------------------------


class TestCalculateActionDuration:
    """Tests for action duration calculation."""

    @pytest.fixture()
    def mining_action(self) -> LifeSkillAction:
        return LifeSkillAction(
            action_id="mine_iron",
            name="Mine Iron Ore",
            skill_type=LifeSkillType.MINING,
            base_duration_seconds=10.0,
            xp_reward=15,
        )

    def test_duration_at_level_1(self, mining_action: LifeSkillAction) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        duration = calculate_action_duration(mining_action, skill)
        assert duration == pytest.approx(10.0)

    def test_duration_at_level_50(self, mining_action: LifeSkillAction) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=50)
        duration = calculate_action_duration(mining_action, skill)
        # 10.0 * 0.755 = 7.55
        assert duration == pytest.approx(7.55)

    def test_minimum_duration_1_second(self) -> None:
        """Even with a very short base and high level, duration floors at 1.0."""
        action = LifeSkillAction(
            action_id="quick_mine",
            name="Quick Mine",
            skill_type=LifeSkillType.MINING,
            base_duration_seconds=0.5,
            xp_reward=5,
        )
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=99)
        duration = calculate_action_duration(action, skill)
        assert duration == 1.0


# ---------------------------------------------------------------------------
# calculate_resource_yield tests
# ---------------------------------------------------------------------------


class TestCalculateResourceYield:
    """Tests for resource yield calculation."""

    @pytest.fixture()
    def iron_action(self) -> LifeSkillAction:
        return LifeSkillAction(
            action_id="mine_iron",
            name="Mine Iron Ore",
            skill_type=LifeSkillType.MINING,
            base_duration_seconds=10.0,
            xp_reward=15,
            resource_yields=[
                ResourceYield(
                    resource_id="iron_ore",
                    resource_name="Iron Ore",
                    quantity=10,
                ),
            ],
        )

    def test_yield_at_level_1_no_bonus(self, iron_action: LifeSkillAction) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING)
        results = calculate_resource_yield(iron_action, skill)
        assert len(results) == 1
        assert results[0].quantity == 10
        assert results[0].bonus_quantity == 0

    def test_yield_at_level_50_with_bonus(self, iron_action: LifeSkillAction) -> None:
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=50)
        results = calculate_resource_yield(iron_action, skill)
        # 10 * 1.49 = 14.9 -> int = 14, bonus = 14 - 10 = 4
        assert results[0].quantity == 10
        assert results[0].bonus_quantity == 4

    def test_yield_multiple_resources(self) -> None:
        action = LifeSkillAction(
            action_id="mine_mixed",
            name="Mine Mixed Vein",
            skill_type=LifeSkillType.MINING,
            base_duration_seconds=20.0,
            xp_reward=25,
            resource_yields=[
                ResourceYield(
                    resource_id="iron_ore",
                    resource_name="Iron Ore",
                    quantity=5,
                ),
                ResourceYield(
                    resource_id="coal",
                    resource_name="Coal",
                    quantity=3,
                ),
            ],
        )
        skill = LifeSkill(skill_type=LifeSkillType.MINING, level=20)
        results = calculate_resource_yield(action, skill)
        assert len(results) == 2
        # Level 20 bonus = 1.19
        # iron: 5 * 1.19 = 5.95 -> 5, bonus = 0
        assert results[0].resource_id == "iron_ore"
        assert results[0].quantity == 5
        assert results[0].bonus_quantity == 0
        # coal: 3 * 1.19 = 3.57 -> 3, bonus = 0
        assert results[1].resource_id == "coal"
        assert results[1].quantity == 3
        assert results[1].bonus_quantity == 0

    def test_yield_empty_resources(self) -> None:
        action = LifeSkillAction(
            action_id="train_strat",
            name="Train Strategy",
            skill_type=LifeSkillType.STRATEGY_TRAINING,
            base_duration_seconds=30.0,
            xp_reward=50,
        )
        skill = LifeSkill(skill_type=LifeSkillType.STRATEGY_TRAINING)
        results = calculate_resource_yield(action, skill)
        assert results == []


# ---------------------------------------------------------------------------
# ResourceYield tests
# ---------------------------------------------------------------------------


class TestResourceYield:
    """Tests for ResourceYield validation."""

    def test_valid_construction(self) -> None:
        ry = ResourceYield(
            resource_id="iron_ore",
            resource_name="Iron Ore",
            quantity=5,
        )
        assert ry.bonus_quantity == 0

    def test_rejects_empty_resource_id(self) -> None:
        with pytest.raises(ValidationError):
            ResourceYield(resource_id="", resource_name="Iron Ore", quantity=5)

    def test_rejects_zero_quantity(self) -> None:
        with pytest.raises(ValidationError):
            ResourceYield(resource_id="iron", resource_name="Iron", quantity=0)
