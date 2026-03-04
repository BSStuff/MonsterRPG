"""Tests for skill progression models."""

import pytest
from pydantic import ValidationError

from monster_rpg.monsters.models import Element
from monster_rpg.skills.progression import Skill, SkillType


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
