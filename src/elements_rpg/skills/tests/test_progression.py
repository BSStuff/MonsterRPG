"""Tests for skill progression models."""

import pytest
from pydantic import ValidationError

from elements_rpg.config import MAX_SKILL_LEVEL
from elements_rpg.monsters.models import Element
from elements_rpg.skills.progression import Skill, SkillMilestone, SkillType, skill_xp_for_level


def _make_skill(**overrides: object) -> Skill:
    """Create a Skill with sensible defaults."""
    defaults: dict[str, object] = {
        "skill_id": "sk_fireball",
        "name": "Fireball",
        "skill_type": SkillType.ATTACK,
        "element": Element.FIRE,
        "power": 80,
        "accuracy": 90,
        "cooldown": 2.5,
        "description": "Hurls a ball of fire at the target.",
    }
    defaults.update(overrides)
    return Skill(**defaults)


def _make_milestone(**overrides: object) -> SkillMilestone:
    """Create a SkillMilestone with sensible defaults."""
    defaults: dict[str, object] = {
        "level_required": 10,
        "name": "Scorching Flames",
        "description": "Increases fire damage by 10%.",
        "bonus_type": "damage",
        "bonus_value": 0.1,
    }
    defaults.update(overrides)
    return SkillMilestone(**defaults)


class TestSkillType:
    """Tests for SkillType enum."""

    def test_all_types(self) -> None:
        """All four skill types should be defined."""
        assert set(SkillType) == {
            SkillType.ATTACK,
            SkillType.DEFENSE,
            SkillType.SUPPORT,
            SkillType.SPECIAL,
        }

    def test_values(self) -> None:
        """Skill type values should be lowercase strings."""
        assert SkillType.ATTACK.value == "attack"
        assert SkillType.SPECIAL.value == "special"


class TestSkill:
    """Tests for Skill model."""

    def test_valid_construction(self) -> None:
        """Skill should accept valid data."""
        skill = _make_skill()
        assert skill.skill_id == "sk_fireball"
        assert skill.name == "Fireball"
        assert skill.skill_type == SkillType.ATTACK
        assert skill.element == Element.FIRE
        assert skill.power == 80
        assert skill.accuracy == 90
        assert skill.cooldown == 2.5

    def test_empty_skill_id_rejected(self) -> None:
        """skill_id cannot be empty."""
        with pytest.raises(ValidationError):
            _make_skill(skill_id="")

    def test_defaults(self) -> None:
        """Level should default to 1, experience to 0."""
        skill = _make_skill()
        assert skill.level == 1
        assert skill.experience == 0

    def test_empty_name_rejected(self) -> None:
        """Name cannot be empty."""
        with pytest.raises(ValidationError):
            _make_skill(name="")

    def test_long_name_rejected(self) -> None:
        """Name cannot exceed 50 characters."""
        with pytest.raises(ValidationError):
            _make_skill(name="X" * 51)

    def test_negative_power_rejected(self) -> None:
        """Power cannot be negative."""
        with pytest.raises(ValidationError):
            _make_skill(power=-1)

    def test_zero_power_allowed(self) -> None:
        """Power of 0 is valid (e.g., support skills)."""
        skill = _make_skill(power=0)
        assert skill.power == 0

    def test_accuracy_bounds(self) -> None:
        """Accuracy must be between 1 and 100."""
        with pytest.raises(ValidationError):
            _make_skill(accuracy=0)
        with pytest.raises(ValidationError):
            _make_skill(accuracy=101)

    def test_negative_cooldown_rejected(self) -> None:
        """Cooldown cannot be negative."""
        with pytest.raises(ValidationError):
            _make_skill(cooldown=-0.5)

    def test_level_bounds(self) -> None:
        """Skill level must be between 1 and 20."""
        with pytest.raises(ValidationError):
            _make_skill(level=0)
        with pytest.raises(ValidationError):
            _make_skill(level=21)

    def test_negative_experience_rejected(self) -> None:
        """Experience cannot be negative."""
        with pytest.raises(ValidationError):
            _make_skill(experience=-1)

    def test_milestones_default_empty(self) -> None:
        """Milestones should default to an empty list."""
        skill = _make_skill()
        assert skill.milestones == []


class TestSkillXpForLevel:
    """Tests for the skill_xp_for_level function."""

    def test_level_1_is_zero(self) -> None:
        """Level 1 requires 0 XP (starting level)."""
        assert skill_xp_for_level(1) == 0

    def test_level_5(self) -> None:
        """Level 5 XP should match formula int(50 * 5^1.3)."""
        expected = int(50 * (5**1.3))
        assert skill_xp_for_level(5) == expected

    def test_level_10(self) -> None:
        """Level 10 XP should match formula."""
        expected = int(50 * (10**1.3))
        assert skill_xp_for_level(10) == expected

    def test_level_15(self) -> None:
        """Level 15 XP should match formula."""
        expected = int(50 * (15**1.3))
        assert skill_xp_for_level(15) == expected

    def test_level_20(self) -> None:
        """Level 20 (max) XP should match formula."""
        expected = int(50 * (20**1.3))
        assert skill_xp_for_level(20) == expected

    def test_monotonically_increasing(self) -> None:
        """XP required should strictly increase with level."""
        for lvl in range(2, MAX_SKILL_LEVEL):
            assert skill_xp_for_level(lvl) < skill_xp_for_level(lvl + 1)

    def test_level_0_raises(self) -> None:
        """Level 0 is invalid."""
        with pytest.raises(ValueError, match="between 1 and"):
            skill_xp_for_level(0)

    def test_level_above_max_raises(self) -> None:
        """Level above max is invalid."""
        with pytest.raises(ValueError, match="between 1 and"):
            skill_xp_for_level(MAX_SKILL_LEVEL + 1)


class TestGainExperience:
    """Tests for Skill.gain_experience method."""

    def test_gain_one_level(self) -> None:
        """Gaining enough XP for level 2 should return [2]."""
        skill = _make_skill()
        xp_needed = skill_xp_for_level(2)
        levels = skill.gain_experience(xp_needed)
        assert levels == [2]
        assert skill.level == 2

    def test_gain_multiple_levels(self) -> None:
        """Gaining enough XP for multiple levels at once."""
        skill = _make_skill()
        # Give enough XP to reach level 5 (sum of costs for levels 2-5)
        xp_needed = sum(skill_xp_for_level(lvl) for lvl in range(2, 6))
        levels = skill.gain_experience(xp_needed)
        assert skill.level == 5
        assert levels == [2, 3, 4, 5]
        assert skill.experience == 0  # Exact amount, no leftover

    def test_caps_at_max_level(self) -> None:
        """XP gain should not exceed max skill level."""
        skill = _make_skill()
        massive_xp = 999_999
        levels = skill.gain_experience(massive_xp)
        assert skill.level == MAX_SKILL_LEVEL
        assert levels[-1] == MAX_SKILL_LEVEL

    def test_no_levels_at_max(self) -> None:
        """Gaining XP at max level returns empty list."""
        skill = _make_skill(level=MAX_SKILL_LEVEL, experience=0)
        levels = skill.gain_experience(100)
        assert levels == []
        assert skill.level == MAX_SKILL_LEVEL

    def test_leftover_xp_retained(self) -> None:
        """XP beyond level threshold should be retained after subtraction."""
        skill = _make_skill()
        xp_for_2 = skill_xp_for_level(2)
        xp_for_3 = skill_xp_for_level(3)
        # Give enough for level 2 plus a bit extra (but not enough for 3)
        extra = xp_for_3 // 2  # Some XP that won't reach level 3
        total_xp = xp_for_2 + extra
        skill.gain_experience(total_xp)
        assert skill.level == 2
        assert skill.experience == extra  # Leftover after subtracting xp_for_2

    def test_negative_xp_raises(self) -> None:
        """Negative XP should raise ValueError."""
        skill = _make_skill()
        with pytest.raises(ValueError, match="positive"):
            skill.gain_experience(-10)

    def test_zero_xp_raises(self) -> None:
        """Zero XP should raise ValueError."""
        skill = _make_skill()
        with pytest.raises(ValueError, match="positive"):
            skill.gain_experience(0)

    def test_incremental_gains(self) -> None:
        """Multiple small XP gains should accumulate correctly."""
        skill = _make_skill()
        xp_for_2 = skill_xp_for_level(2)
        # Add XP in two halves
        skill.gain_experience(xp_for_2 // 2)
        assert skill.level == 1
        levels = skill.gain_experience(xp_for_2 - xp_for_2 // 2)
        assert skill.level == 2
        assert 2 in levels


class TestSkillMilestone:
    """Tests for SkillMilestone model."""

    def test_valid_construction(self) -> None:
        """Milestone should accept valid data."""
        ms = _make_milestone()
        assert ms.level_required == 10
        assert ms.name == "Scorching Flames"
        assert ms.bonus_type == "damage"
        assert ms.bonus_value == 0.1

    def test_level_required_minimum(self) -> None:
        """level_required must be >= 1."""
        with pytest.raises(ValidationError):
            _make_milestone(level_required=0)

    def test_empty_name_rejected(self) -> None:
        """Milestone name cannot be empty."""
        with pytest.raises(ValidationError):
            _make_milestone(name="")


class TestUnlockedMilestones:
    """Tests for Skill.unlocked_milestones method."""

    def test_empty_at_level_1(self) -> None:
        """No milestones should be unlocked at level 1."""
        milestones = [
            _make_milestone(level_required=10),
            _make_milestone(level_required=25, name="Advanced Flames"),
        ]
        skill = _make_skill(milestones=milestones)
        assert skill.unlocked_milestones() == []

    def test_unlocked_at_level_10(self) -> None:
        """Milestone at level 10 should be unlocked when skill is level 10."""
        ms_10 = _make_milestone(level_required=10)
        ms_25 = _make_milestone(level_required=25, name="Advanced Flames")
        skill = _make_skill(level=10, milestones=[ms_10, ms_25])
        unlocked = skill.unlocked_milestones()
        assert len(unlocked) == 1
        assert unlocked[0].level_required == 10

    def test_multiple_unlocked(self) -> None:
        """Multiple milestones can be unlocked at high levels."""
        ms_5 = _make_milestone(level_required=5, name="Minor Boost")
        ms_10 = _make_milestone(level_required=10)
        skill = _make_skill(level=15, milestones=[ms_5, ms_10])
        assert len(skill.unlocked_milestones()) == 2

    def test_no_milestones_defined(self) -> None:
        """Skill with no milestones returns empty list."""
        skill = _make_skill()
        assert skill.unlocked_milestones() == []


class TestNextMilestone:
    """Tests for Skill.next_milestone method."""

    def test_returns_first_at_level_1(self) -> None:
        """At level 1, next milestone should be the lowest-level one."""
        ms_10 = _make_milestone(level_required=10)
        ms_25 = _make_milestone(level_required=25, name="Advanced Flames")
        skill = _make_skill(milestones=[ms_10, ms_25])
        nxt = skill.next_milestone()
        assert nxt is not None
        assert nxt.level_required == 10

    def test_returns_none_all_unlocked(self) -> None:
        """Returns None when all milestones are unlocked."""
        ms_5 = _make_milestone(level_required=5, name="Minor Boost")
        skill = _make_skill(level=10, milestones=[ms_5])
        assert skill.next_milestone() is None

    def test_returns_none_no_milestones(self) -> None:
        """Returns None when skill has no milestones."""
        skill = _make_skill()
        assert skill.next_milestone() is None

    def test_skips_already_unlocked(self) -> None:
        """Next milestone should skip already-unlocked ones."""
        ms_5 = _make_milestone(level_required=5, name="Minor Boost")
        ms_10 = _make_milestone(level_required=10)
        ms_25 = _make_milestone(level_required=25, name="Advanced Flames")
        skill = _make_skill(level=10, milestones=[ms_5, ms_10, ms_25])
        nxt = skill.next_milestone()
        assert nxt is not None
        assert nxt.level_required == 25


class TestEffectivePower:
    """Tests for Skill.effective_power method."""

    def test_level_1_equals_base(self) -> None:
        """At level 1, effective power equals base power."""
        skill = _make_skill(power=100)
        assert skill.effective_power() == 100

    def test_level_10_bonus(self) -> None:
        """At level 10, effective power has 18% bonus (9 levels * 2%)."""
        skill = _make_skill(power=100, level=10)
        # 100 * 1.18 = 118
        assert skill.effective_power() == 118

    def test_level_20_bonus(self) -> None:
        """At level 20, effective power has 38% bonus."""
        skill = _make_skill(power=100, level=20)
        # 100 * 1.38 = 138
        assert skill.effective_power() == 138

    def test_zero_power_stays_zero(self) -> None:
        """Zero base power stays zero regardless of level."""
        skill = _make_skill(power=0, level=10)
        assert skill.effective_power() == 0


class TestEffectiveCooldown:
    """Tests for Skill.effective_cooldown method."""

    def test_level_1_equals_base(self) -> None:
        """At level 1, effective cooldown equals base cooldown."""
        skill = _make_skill(cooldown=2.5)
        assert skill.effective_cooldown() == 2.5

    def test_level_20_reduction(self) -> None:
        """At level 20, cooldown is reduced by 19% (19 levels * 1%)."""
        skill = _make_skill(cooldown=2.5, level=20)
        # 2.5 * 0.81 = 2.025
        assert skill.effective_cooldown() == pytest.approx(2.025)

    def test_minimum_cooldown(self) -> None:
        """Effective cooldown should not go below 0.5 seconds."""
        skill = _make_skill(cooldown=0.5, level=20)
        assert skill.effective_cooldown() >= 0.5

    def test_zero_cooldown_returns_minimum(self) -> None:
        """Zero base cooldown returns minimum 0.5 at any level."""
        skill = _make_skill(cooldown=0.0, level=10)
        assert skill.effective_cooldown() == 0.5

    def test_level_10_reduction(self) -> None:
        """At level 10, cooldown is reduced by 9%."""
        skill = _make_skill(cooldown=10.0, level=10)
        # 10.0 * 0.91 = 9.1
        assert skill.effective_cooldown() == pytest.approx(9.1)
