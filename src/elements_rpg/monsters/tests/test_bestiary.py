"""Tests for MVP monster bestiary definitions."""

from collections import Counter

import pytest

from elements_rpg.monsters.bestiary import (
    CRYSTAL_CAVERNS_SPECIES,
    MVP_SPECIES,
    VERDANT_MEADOWS_SPECIES,
)
from elements_rpg.monsters.models import Element, Rarity
from elements_rpg.monsters.skill_catalog import MVP_SKILLS


class TestBestiarySize:
    """Tests for bestiary completeness."""

    def test_mvp_species_has_12_entries(self) -> None:
        assert len(MVP_SPECIES) == 12

    def test_verdant_meadows_has_6_species(self) -> None:
        assert len(VERDANT_MEADOWS_SPECIES) == 6

    def test_crystal_caverns_has_6_species(self) -> None:
        assert len(CRYSTAL_CAVERNS_SPECIES) == 6

    def test_all_area_species_in_mvp(self) -> None:
        all_area = set(VERDANT_MEADOWS_SPECIES + CRYSTAL_CAVERNS_SPECIES)
        assert all_area == set(MVP_SPECIES.keys())

    def test_no_overlap_between_areas(self) -> None:
        overlap = set(VERDANT_MEADOWS_SPECIES) & set(CRYSTAL_CAVERNS_SPECIES)
        assert len(overlap) == 0, f"Shared species between areas: {overlap}"


class TestUniqueness:
    """Tests for unique IDs and names."""

    def test_all_species_have_unique_ids(self) -> None:
        ids = [s.species_id for s in MVP_SPECIES.values()]
        assert len(ids) == len(set(ids))

    def test_all_species_have_unique_names(self) -> None:
        names = [s.name for s in MVP_SPECIES.values()]
        assert len(names) == len(set(names))


class TestElementDistribution:
    """Tests for element distribution across the bestiary."""

    def test_element_counts(self) -> None:
        elements = [s.element for s in MVP_SPECIES.values()]
        counts = Counter(elements)
        assert counts[Element.EARTH] == 3
        assert counts[Element.FIRE] == 2
        assert counts[Element.WATER] == 2
        assert counts[Element.WIND] == 3
        assert counts[Element.NEUTRAL] == 2


class TestRarityDistribution:
    """Tests for rarity distribution across the bestiary."""

    def test_rarity_counts(self) -> None:
        rarities = [s.rarity for s in MVP_SPECIES.values()]
        counts = Counter(rarities)
        assert counts[Rarity.COMMON] == 4
        assert counts[Rarity.UNCOMMON] == 4
        assert counts[Rarity.RARE] == 3
        assert counts[Rarity.EPIC] == 1


# Rarity -> (min_total, max_total) for base stat totals
RARITY_STAT_RANGES: dict[Rarity, tuple[int, int]] = {
    Rarity.COMMON: (240, 320),
    Rarity.UNCOMMON: (260, 370),
    Rarity.RARE: (300, 420),
    Rarity.EPIC: (320, 480),
}


class TestStatTotals:
    """Tests for stat totals matching rarity guidelines."""

    @pytest.mark.parametrize(
        "species_id",
        list(MVP_SPECIES.keys()),
    )
    def test_stat_total_in_rarity_range(self, species_id: str) -> None:
        species = MVP_SPECIES[species_id]
        stats = species.base_stats
        total = stats.hp + stats.attack + stats.defense + stats.speed
        total += stats.magic_attack + stats.magic_defense
        min_t, max_t = RARITY_STAT_RANGES[species.rarity]
        assert min_t <= total <= max_t, (
            f"{species.name} ({species.rarity}) total={total}, expected {min_t}-{max_t}"
        )


class TestLearnableSkills:
    """Tests for learnable skill assignments."""

    @pytest.mark.parametrize(
        "species_id",
        list(MVP_SPECIES.keys()),
    )
    def test_each_species_has_4_learnable_skills(self, species_id: str) -> None:
        species = MVP_SPECIES[species_id]
        assert len(species.learnable_skill_ids) == 4, (
            f"{species.name} has {len(species.learnable_skill_ids)} skills, expected 4"
        )

    @pytest.mark.parametrize(
        "species_id",
        list(MVP_SPECIES.keys()),
    )
    def test_all_learnable_skill_ids_exist_in_catalog(self, species_id: str) -> None:
        species = MVP_SPECIES[species_id]
        for skill_id in species.learnable_skill_ids:
            assert skill_id in MVP_SKILLS, f"{species.name} references missing skill '{skill_id}'"

    @pytest.mark.parametrize(
        "species_id",
        list(MVP_SPECIES.keys()),
    )
    def test_no_duplicate_learnable_skills(self, species_id: str) -> None:
        species = MVP_SPECIES[species_id]
        assert len(species.learnable_skill_ids) == len(set(species.learnable_skill_ids))


class TestSpeciesIds:
    """Tests that species IDs match the expected format for area integration."""

    EXPECTED_IDS = [
        "species_leaflet",
        "species_ember_pup",
        "species_breeze_sprite",
        "species_pebble_crab",
        "species_dewdrop_slime",
        "species_meadow_fox",
        "species_crystal_bat",
        "species_magma_wyrm",
        "species_aqua_serpent",
        "species_shadow_moth",
        "species_geo_golem",
        "species_prism_fairy",
    ]

    @pytest.mark.parametrize("expected_id", EXPECTED_IDS)
    def test_expected_species_id_present(self, expected_id: str) -> None:
        assert expected_id in MVP_SPECIES, f"Missing expected species: {expected_id}"


class TestPassiveTraits:
    """Tests that all species have valid passive traits."""

    def test_all_species_have_passive_trait(self) -> None:
        for species in MVP_SPECIES.values():
            assert len(species.passive_trait) > 0, f"{species.name} missing passive trait"

    def test_all_species_have_passive_description(self) -> None:
        for species in MVP_SPECIES.values():
            assert len(species.passive_description) > 0, (
                f"{species.name} missing passive description"
            )

    def test_all_passive_traits_unique(self) -> None:
        traits = [s.passive_trait for s in MVP_SPECIES.values()]
        assert len(traits) == len(set(traits)), "Duplicate passive traits found"
