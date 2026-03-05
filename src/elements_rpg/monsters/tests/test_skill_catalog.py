"""Tests for MVP skill catalog definitions."""

from collections import Counter

import pytest

from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.models import Element
from elements_rpg.monsters.skill_catalog import MVP_SKILLS
from elements_rpg.skills.progression import SkillType


class TestCatalogSize:
    """Tests for catalog completeness."""

    def test_mvp_skills_has_at_least_16_entries(self) -> None:
        assert len(MVP_SKILLS) >= 16, f"Only {len(MVP_SKILLS)} skills, need at least 16"

    def test_all_skills_have_unique_ids(self) -> None:
        ids = [s.skill_id for s in MVP_SKILLS.values()]
        assert len(ids) == len(set(ids))

    def test_all_skills_have_unique_names(self) -> None:
        names = [s.name for s in MVP_SKILLS.values()]
        assert len(names) == len(set(names))


class TestSkillTypeRepresentation:
    """Tests that all skill types are represented."""

    def test_all_skill_types_present(self) -> None:
        types = {s.skill_type for s in MVP_SKILLS.values()}
        for skill_type in SkillType:
            assert skill_type in types, f"Missing skill type: {skill_type}"

    def test_skill_type_distribution(self) -> None:
        types = [s.skill_type for s in MVP_SKILLS.values()]
        counts = Counter(types)
        # At least 2 of each type
        for skill_type in SkillType:
            assert counts[skill_type] >= 2, (
                f"Only {counts[skill_type]} {skill_type} skills, need at least 2"
            )


class TestElementRepresentation:
    """Tests that all elements are represented in skills."""

    def test_all_elements_present(self) -> None:
        elements = {s.element for s in MVP_SKILLS.values()}
        for element in Element:
            assert element in elements, f"Missing element: {element}"

    def test_element_distribution(self) -> None:
        elements = [s.element for s in MVP_SKILLS.values()]
        counts = Counter(elements)
        # At least 2 skills per element
        for element in Element:
            assert counts[element] >= 2, f"Only {counts[element]} {element} skills, need at least 2"


class TestSkillRanges:
    """Tests that skill stats are within reasonable ranges."""

    @pytest.mark.parametrize("skill_id", list(MVP_SKILLS.keys()))
    def test_skill_power_range(self, skill_id: str) -> None:
        skill = MVP_SKILLS[skill_id]
        assert 0 <= skill.power <= 120, f"{skill.name} power={skill.power}, expected 0-120"

    @pytest.mark.parametrize("skill_id", list(MVP_SKILLS.keys()))
    def test_skill_accuracy_range(self, skill_id: str) -> None:
        skill = MVP_SKILLS[skill_id]
        assert 50 <= skill.accuracy <= 100, (
            f"{skill.name} accuracy={skill.accuracy}, expected 50-100"
        )

    @pytest.mark.parametrize("skill_id", list(MVP_SKILLS.keys()))
    def test_skill_cooldown_positive(self, skill_id: str) -> None:
        skill = MVP_SKILLS[skill_id]
        assert skill.cooldown > 0, f"{skill.name} has non-positive cooldown"


class TestMonsterSkillIntegration:
    """Tests that every monster's learnable skills exist in the catalog."""

    @pytest.mark.parametrize("species_id", list(MVP_SPECIES.keys()))
    def test_monster_skills_in_catalog(self, species_id: str) -> None:
        species = MVP_SPECIES[species_id]
        for skill_id in species.learnable_skill_ids:
            assert skill_id in MVP_SKILLS, (
                f"{species.name} references '{skill_id}' not in MVP_SKILLS"
            )


class TestSkillMilestones:
    """Tests that skill milestones are well-formed."""

    def test_all_skills_have_milestones(self) -> None:
        for skill in MVP_SKILLS.values():
            assert len(skill.milestones) >= 1, f"{skill.name} has no milestones"

    @pytest.mark.parametrize("skill_id", list(MVP_SKILLS.keys()))
    def test_milestone_levels_positive(self, skill_id: str) -> None:
        skill = MVP_SKILLS[skill_id]
        for ms in skill.milestones:
            assert ms.level_required >= 1, (
                f"{skill.name} milestone '{ms.name}' has level_required < 1"
            )

    @pytest.mark.parametrize("skill_id", list(MVP_SKILLS.keys()))
    def test_milestone_bonus_values_positive(self, skill_id: str) -> None:
        skill = MVP_SKILLS[skill_id]
        for ms in skill.milestones:
            assert ms.bonus_value > 0, (
                f"{skill.name} milestone '{ms.name}' has non-positive bonus_value"
            )


class TestSkillDescriptions:
    """Tests that all skills have descriptions."""

    def test_all_skills_have_descriptions(self) -> None:
        for skill in MVP_SKILLS.values():
            assert len(skill.description) > 0, f"{skill.name} missing description"
