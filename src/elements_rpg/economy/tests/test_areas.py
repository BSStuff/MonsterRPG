"""Tests for MVP area definitions and drop table system."""

import pytest
from pydantic import ValidationError

from elements_rpg.economy.areas import (
    CRYSTAL_CAVERNS,
    CRYSTAL_CAVERNS_DROPS,
    MVP_AREAS,
    MVP_DROP_TABLES,
    MVP_MATERIALS,
    VERDANT_MEADOWS,
    VERDANT_MEADOWS_DROPS,
    AreaDropTable,
    DropTableEntry,
)
from elements_rpg.economy.manager import AreaDifficulty

# ==========================================
# DropTableEntry Tests
# ==========================================


class TestDropTableEntry:
    """Tests for DropTableEntry construction and validation."""

    def test_valid_entry(self) -> None:
        entry = DropTableEntry(
            material_id="mat_test",
            drop_chance=0.5,
            min_quantity=1,
            max_quantity=3,
        )
        assert entry.material_id == "mat_test"
        assert entry.drop_chance == 0.5
        assert entry.min_quantity == 1
        assert entry.max_quantity == 3
        assert entry.difficulty_required is None

    def test_entry_with_difficulty_required(self) -> None:
        entry = DropTableEntry(
            material_id="mat_test",
            drop_chance=0.1,
            difficulty_required=AreaDifficulty.HARD,
        )
        assert entry.difficulty_required == AreaDifficulty.HARD

    def test_drop_chance_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            DropTableEntry(material_id="mat_test", drop_chance=0.0)

    def test_drop_chance_must_be_at_most_one(self) -> None:
        with pytest.raises(ValidationError):
            DropTableEntry(material_id="mat_test", drop_chance=1.5)

    def test_drop_chance_exactly_one_is_valid(self) -> None:
        entry = DropTableEntry(material_id="mat_test", drop_chance=1.0)
        assert entry.drop_chance == 1.0

    def test_material_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError):
            DropTableEntry(material_id="", drop_chance=0.5)

    def test_min_quantity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            DropTableEntry(material_id="mat_test", drop_chance=0.5, min_quantity=0)

    def test_max_quantity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            DropTableEntry(material_id="mat_test", drop_chance=0.5, max_quantity=0)

    def test_defaults(self) -> None:
        entry = DropTableEntry(material_id="mat_test", drop_chance=0.5)
        assert entry.min_quantity == 1
        assert entry.max_quantity == 1
        assert entry.difficulty_required is None

    def test_drop_table_entry_min_exceeds_max_raises(self) -> None:
        with pytest.raises(ValidationError, match="min_quantity"):
            DropTableEntry(
                material_id="mat_test",
                drop_chance=0.5,
                min_quantity=5,
                max_quantity=2,
            )


# ==========================================
# AreaDropTable Tests
# ==========================================


class TestAreaDropTable:
    """Tests for AreaDropTable and difficulty filtering."""

    def test_empty_drop_table(self) -> None:
        table = AreaDropTable(area_id="area_test")
        assert table.entries == []
        assert table.get_drops_for_difficulty(AreaDifficulty.EASY) == []

    def test_get_drops_no_difficulty_requirement(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(material_id="mat_a", drop_chance=0.5),
                DropTableEntry(material_id="mat_b", drop_chance=0.3),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.EASY)
        assert len(drops) == 2

    def test_easy_excludes_medium_required(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(material_id="mat_a", drop_chance=0.5),
                DropTableEntry(
                    material_id="mat_b",
                    drop_chance=0.1,
                    difficulty_required=AreaDifficulty.MEDIUM,
                ),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.EASY)
        assert len(drops) == 1
        assert drops[0].material_id == "mat_a"

    def test_medium_includes_medium_required(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(material_id="mat_a", drop_chance=0.5),
                DropTableEntry(
                    material_id="mat_b",
                    drop_chance=0.1,
                    difficulty_required=AreaDifficulty.MEDIUM,
                ),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.MEDIUM)
        assert len(drops) == 2

    def test_hard_includes_medium_and_hard_required(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(material_id="mat_a", drop_chance=0.5),
                DropTableEntry(
                    material_id="mat_b",
                    drop_chance=0.1,
                    difficulty_required=AreaDifficulty.MEDIUM,
                ),
                DropTableEntry(
                    material_id="mat_c",
                    drop_chance=0.05,
                    difficulty_required=AreaDifficulty.HARD,
                ),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.HARD)
        assert len(drops) == 3

    def test_boss_includes_all(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(material_id="mat_a", drop_chance=0.5),
                DropTableEntry(
                    material_id="mat_b",
                    drop_chance=0.1,
                    difficulty_required=AreaDifficulty.HARD,
                ),
                DropTableEntry(
                    material_id="mat_c",
                    drop_chance=0.05,
                    difficulty_required=AreaDifficulty.BOSS,
                ),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.BOSS)
        assert len(drops) == 3

    def test_easy_excludes_hard_required(self) -> None:
        table = AreaDropTable(
            area_id="area_test",
            entries=[
                DropTableEntry(
                    material_id="mat_rare",
                    drop_chance=0.05,
                    difficulty_required=AreaDifficulty.HARD,
                ),
            ],
        )
        drops = table.get_drops_for_difficulty(AreaDifficulty.EASY)
        assert len(drops) == 0

    def test_area_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError):
            AreaDropTable(area_id="")


# ==========================================
# MVP Area Definition Tests
# ==========================================


class TestMVPAreas:
    """Tests for the MVP area constants."""

    def test_mvp_areas_has_two_areas(self) -> None:
        assert len(MVP_AREAS) == 2

    def test_verdant_meadows_properties(self) -> None:
        area = VERDANT_MEADOWS
        assert area.area_id == "area_verdant_meadows"
        assert area.name == "Verdant Meadows"
        assert area.difficulty == AreaDifficulty.EASY
        assert area.recommended_level == 1

    def test_verdant_meadows_has_six_monsters(self) -> None:
        assert len(VERDANT_MEADOWS.monster_species_ids) == 6

    def test_verdant_meadows_has_four_materials(self) -> None:
        assert len(VERDANT_MEADOWS.material_drop_ids) == 4

    def test_crystal_caverns_properties(self) -> None:
        area = CRYSTAL_CAVERNS
        assert area.area_id == "area_crystal_caverns"
        assert area.name == "Crystal Caverns"
        assert area.difficulty == AreaDifficulty.MEDIUM
        assert area.recommended_level == 15

    def test_crystal_caverns_has_six_monsters(self) -> None:
        assert len(CRYSTAL_CAVERNS.monster_species_ids) == 6

    def test_crystal_caverns_has_four_materials(self) -> None:
        assert len(CRYSTAL_CAVERNS.material_drop_ids) == 4

    def test_areas_have_unique_monsters(self) -> None:
        meadow_monsters = set(VERDANT_MEADOWS.monster_species_ids)
        cavern_monsters = set(CRYSTAL_CAVERNS.monster_species_ids)
        assert meadow_monsters.isdisjoint(cavern_monsters)

    def test_areas_have_unique_materials(self) -> None:
        meadow_mats = set(VERDANT_MEADOWS.material_drop_ids)
        cavern_mats = set(CRYSTAL_CAVERNS.material_drop_ids)
        assert meadow_mats.isdisjoint(cavern_mats)


# ==========================================
# MVP Materials Tests
# ==========================================


class TestMVPMaterials:
    """Tests for the MVP material constants."""

    def test_mvp_materials_has_eight(self) -> None:
        assert len(MVP_MATERIALS) == 8

    def test_all_material_sell_prices_positive(self) -> None:
        for mat_id, mat in MVP_MATERIALS.items():
            assert mat.sell_price > 0, f"{mat_id} has non-positive sell price"

    def test_all_material_ids_match_keys(self) -> None:
        for key, mat in MVP_MATERIALS.items():
            assert key == mat.material_id

    def test_all_area_materials_exist_in_mvp_materials(self) -> None:
        for area in MVP_AREAS.values():
            for mat_id in area.material_drop_ids:
                assert mat_id in MVP_MATERIALS, f"{mat_id} not in MVP_MATERIALS"


# ==========================================
# Drop Table Tests
# ==========================================


class TestMVPDropTables:
    """Tests for the MVP drop table constants."""

    def test_mvp_drop_tables_has_two(self) -> None:
        assert len(MVP_DROP_TABLES) == 2

    def test_verdant_meadows_drops_has_four_entries(self) -> None:
        assert len(VERDANT_MEADOWS_DROPS.entries) == 4

    def test_crystal_caverns_drops_has_four_entries(self) -> None:
        assert len(CRYSTAL_CAVERNS_DROPS.entries) == 4

    def test_all_drop_chances_valid(self) -> None:
        for table in MVP_DROP_TABLES.values():
            for entry in table.entries:
                assert 0.0 < entry.drop_chance <= 1.0, (
                    f"{entry.material_id} has invalid drop chance {entry.drop_chance}"
                )

    def test_all_drop_materials_exist_in_mvp_materials(self) -> None:
        for table in MVP_DROP_TABLES.values():
            for entry in table.entries:
                assert entry.material_id in MVP_MATERIALS, (
                    f"{entry.material_id} not in MVP_MATERIALS"
                )

    def test_drop_table_area_ids_match_mvp_areas(self) -> None:
        for area_id in MVP_DROP_TABLES:
            assert area_id in MVP_AREAS, f"{area_id} not in MVP_AREAS"

    def test_verdant_meadows_easy_drops_exclude_meadow_flower(self) -> None:
        drops = VERDANT_MEADOWS_DROPS.get_drops_for_difficulty(AreaDifficulty.EASY)
        mat_ids = [d.material_id for d in drops]
        assert "mat_meadow_flower" not in mat_ids

    def test_verdant_meadows_medium_drops_include_meadow_flower(self) -> None:
        drops = VERDANT_MEADOWS_DROPS.get_drops_for_difficulty(AreaDifficulty.MEDIUM)
        mat_ids = [d.material_id for d in drops]
        assert "mat_meadow_flower" in mat_ids

    def test_crystal_caverns_medium_drops_exclude_luminous_gem(self) -> None:
        drops = CRYSTAL_CAVERNS_DROPS.get_drops_for_difficulty(AreaDifficulty.MEDIUM)
        mat_ids = [d.material_id for d in drops]
        assert "mat_luminous_gem" not in mat_ids

    def test_crystal_caverns_hard_drops_include_luminous_gem(self) -> None:
        drops = CRYSTAL_CAVERNS_DROPS.get_drops_for_difficulty(AreaDifficulty.HARD)
        mat_ids = [d.material_id for d in drops]
        assert "mat_luminous_gem" in mat_ids
