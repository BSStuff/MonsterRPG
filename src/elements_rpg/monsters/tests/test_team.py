"""Tests for the team system — composition, roles, management."""

import pytest
from pydantic import ValidationError

from elements_rpg.config import MAX_TEAM_SIZE
from elements_rpg.monsters.models import (
    Element,
    Monster,
    MonsterSpecies,
    Rarity,
    StatBlock,
)
from elements_rpg.monsters.team import Team, TeamRole, TeamSlot

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def species() -> MonsterSpecies:
    """A basic monster species for building test monsters."""
    return MonsterSpecies(
        species_id="sp_wolf",
        name="Wolf",
        element=Element.NEUTRAL,
        rarity=Rarity.COMMON,
        base_stats=StatBlock(
            hp=100, attack=20, defense=15, speed=18, magic_attack=5, magic_defense=10
        ),
        passive_trait="Pack Hunter",
        passive_description="Gains +10% ATK when allies are present.",
    )


@pytest.fixture()
def empty_team() -> Team:
    """An empty team."""
    return Team(team_id="team_1")


@pytest.fixture()
def three_monster_team() -> Team:
    """A team with 3 monsters pre-loaded."""
    return Team(
        team_id="team_2",
        name="Alpha Squad",
        slots=[
            TeamSlot(monster_id="m1", role=TeamRole.TANK, position=0),
            TeamSlot(monster_id="m2", role=TeamRole.DPS, position=1),
            TeamSlot(monster_id="m3", role=TeamRole.SUPPORT, position=2),
        ],
    )


# ---------------------------------------------------------------------------
# TeamRole enum
# ---------------------------------------------------------------------------


class TestTeamRole:
    def test_all_roles_exist(self) -> None:
        assert set(TeamRole) == {
            TeamRole.TANK,
            TeamRole.OFF_TANK,
            TeamRole.DPS,
            TeamRole.SUPPORT,
            TeamRole.FLEX,
        }

    def test_role_values(self) -> None:
        assert TeamRole.TANK == "tank"
        assert TeamRole.OFF_TANK == "off_tank"
        assert TeamRole.DPS == "dps"
        assert TeamRole.SUPPORT == "support"
        assert TeamRole.FLEX == "flex"


# ---------------------------------------------------------------------------
# TeamSlot construction
# ---------------------------------------------------------------------------


class TestTeamSlot:
    def test_valid_slot(self) -> None:
        slot = TeamSlot(monster_id="m1", role=TeamRole.TANK, position=0)
        assert slot.monster_id == "m1"
        assert slot.role == TeamRole.TANK
        assert slot.position == 0

    def test_slot_no_role(self) -> None:
        slot = TeamSlot(monster_id="m1", position=3)
        assert slot.role is None

    def test_slot_rejects_empty_id(self) -> None:
        with pytest.raises(ValidationError):
            TeamSlot(monster_id="", position=0)

    def test_slot_rejects_invalid_position(self) -> None:
        with pytest.raises(ValidationError):
            TeamSlot(monster_id="m1", position=-1)
        with pytest.raises(ValidationError):
            TeamSlot(monster_id="m1", position=6)


# ---------------------------------------------------------------------------
# Team construction and defaults
# ---------------------------------------------------------------------------


class TestTeamConstruction:
    def test_defaults(self, empty_team: Team) -> None:
        assert empty_team.team_id == "team_1"
        assert empty_team.name == "Team 1"
        assert empty_team.slots == []

    def test_custom_name(self) -> None:
        team = Team(team_id="t", name="My Team")
        assert team.name == "My Team"

    def test_rejects_empty_team_id(self) -> None:
        with pytest.raises(ValidationError):
            Team(team_id="")

    def test_rejects_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            Team(team_id="t", name="x" * 31)


# ---------------------------------------------------------------------------
# Team size validation
# ---------------------------------------------------------------------------


class TestTeamSizeValidation:
    def test_validate_team_size_rejects_over_max(self) -> None:
        slots = [TeamSlot(monster_id=f"m{i}", position=min(i, 5)) for i in range(MAX_TEAM_SIZE + 1)]
        with pytest.raises(ValidationError):
            Team(team_id="t", slots=slots)

    def test_validate_no_duplicate_monsters(self) -> None:
        with pytest.raises(ValidationError, match="duplicate monster"):
            Team(
                team_id="t",
                slots=[
                    TeamSlot(monster_id="m1", position=0),
                    TeamSlot(monster_id="m1", position=1),
                ],
            )

    def test_validate_no_duplicate_positions(self) -> None:
        with pytest.raises(ValidationError, match="share positions"):
            Team(
                team_id="t",
                slots=[
                    TeamSlot(monster_id="m1", position=0),
                    TeamSlot(monster_id="m2", position=0),
                ],
            )


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestTeamProperties:
    def test_size(self, three_monster_team: Team) -> None:
        assert three_monster_team.size == 3

    def test_is_full_false(self, three_monster_team: Team) -> None:
        assert three_monster_team.is_full is False

    def test_is_full_true(self) -> None:
        slots = [TeamSlot(monster_id=f"m{i}", position=i) for i in range(MAX_TEAM_SIZE)]
        team = Team(team_id="t", slots=slots)
        assert team.is_full is True

    def test_is_empty_true(self, empty_team: Team) -> None:
        assert empty_team.is_empty is True

    def test_is_empty_false(self, three_monster_team: Team) -> None:
        assert three_monster_team.is_empty is False

    def test_monster_ids(self, three_monster_team: Team) -> None:
        assert three_monster_team.monster_ids == ["m1", "m2", "m3"]


# ---------------------------------------------------------------------------
# add_monster
# ---------------------------------------------------------------------------


class TestAddMonster:
    def test_add_succeeds(self, empty_team: Team) -> None:
        assert empty_team.add_monster("m1") is True
        assert empty_team.size == 1
        assert empty_team.monster_ids == ["m1"]

    def test_add_with_role(self, empty_team: Team) -> None:
        empty_team.add_monster("m1", role=TeamRole.TANK)
        assert empty_team.slots[0].role == TeamRole.TANK

    def test_add_assigns_correct_position(self, empty_team: Team) -> None:
        empty_team.add_monster("m1")
        empty_team.add_monster("m2")
        assert empty_team.slots[0].position == 0
        assert empty_team.slots[1].position == 1

    def test_add_prevents_duplicates(self, empty_team: Team) -> None:
        empty_team.add_monster("m1")
        assert empty_team.add_monster("m1") is False
        assert empty_team.size == 1

    def test_add_fails_when_full(self) -> None:
        slots = [TeamSlot(monster_id=f"m{i}", position=i) for i in range(MAX_TEAM_SIZE)]
        team = Team(team_id="t", slots=slots)
        assert team.add_monster("new_monster") is False
        assert team.size == MAX_TEAM_SIZE


# ---------------------------------------------------------------------------
# remove_monster
# ---------------------------------------------------------------------------


class TestRemoveMonster:
    def test_remove_succeeds(self, three_monster_team: Team) -> None:
        assert three_monster_team.remove_monster("m2") is True
        assert three_monster_team.size == 2
        assert "m2" not in three_monster_team.monster_ids

    def test_remove_reindexes_positions(self, three_monster_team: Team) -> None:
        three_monster_team.remove_monster("m1")
        assert [s.position for s in three_monster_team.slots] == [0, 1]
        assert three_monster_team.monster_ids == ["m2", "m3"]

    def test_remove_returns_false_for_unknown(self, three_monster_team: Team) -> None:
        assert three_monster_team.remove_monster("unknown") is False
        assert three_monster_team.size == 3


# ---------------------------------------------------------------------------
# reorder
# ---------------------------------------------------------------------------


class TestReorder:
    def test_reorder_succeeds(self, three_monster_team: Team) -> None:
        assert three_monster_team.reorder(["m3", "m1", "m2"]) is True
        assert three_monster_team.monster_ids == ["m3", "m1", "m2"]
        assert [s.position for s in three_monster_team.slots] == [0, 1, 2]

    def test_reorder_fails_with_wrong_ids(self, three_monster_team: Team) -> None:
        assert three_monster_team.reorder(["m3", "m1", "m99"]) is False

    def test_reorder_fails_with_missing_ids(self, three_monster_team: Team) -> None:
        assert three_monster_team.reorder(["m3", "m1"]) is False

    def test_reorder_fails_with_extra_ids(self, three_monster_team: Team) -> None:
        assert three_monster_team.reorder(["m3", "m1", "m2", "m4"]) is False

    def test_reorder_preserves_roles(self, three_monster_team: Team) -> None:
        three_monster_team.reorder(["m3", "m2", "m1"])
        roles = {s.monster_id: s.role for s in three_monster_team.slots}
        assert roles["m1"] == TeamRole.TANK
        assert roles["m2"] == TeamRole.DPS
        assert roles["m3"] == TeamRole.SUPPORT


# ---------------------------------------------------------------------------
# set_role
# ---------------------------------------------------------------------------


class TestSetRole:
    def test_set_role_assigns(self, three_monster_team: Team) -> None:
        assert three_monster_team.set_role("m1", TeamRole.FLEX) is True
        assert three_monster_team.slots[0].role == TeamRole.FLEX

    def test_set_role_clears(self, three_monster_team: Team) -> None:
        assert three_monster_team.set_role("m1", None) is True
        assert three_monster_team.slots[0].role is None

    def test_set_role_returns_false_for_unknown(self, three_monster_team: Team) -> None:
        assert three_monster_team.set_role("unknown", TeamRole.DPS) is False


# ---------------------------------------------------------------------------
# get_monsters_by_role
# ---------------------------------------------------------------------------


class TestGetMonstersByRole:
    def test_filters_correctly(self, three_monster_team: Team) -> None:
        assert three_monster_team.get_monsters_by_role(TeamRole.DPS) == ["m2"]
        assert three_monster_team.get_monsters_by_role(TeamRole.TANK) == ["m1"]

    def test_returns_empty_for_no_match(self, three_monster_team: Team) -> None:
        assert three_monster_team.get_monsters_by_role(TeamRole.FLEX) == []

    def test_returns_multiple(self) -> None:
        team = Team(
            team_id="t",
            slots=[
                TeamSlot(monster_id="m1", role=TeamRole.DPS, position=0),
                TeamSlot(monster_id="m2", role=TeamRole.DPS, position=1),
            ],
        )
        assert team.get_monsters_by_role(TeamRole.DPS) == ["m1", "m2"]


# ---------------------------------------------------------------------------
# get_team_monsters
# ---------------------------------------------------------------------------


class TestGetTeamMonsters:
    def test_returns_monsters_in_order(
        self, three_monster_team: Team, species: MonsterSpecies
    ) -> None:
        registry: dict[str, Monster] = {}
        for mid in ["m1", "m2", "m3"]:
            registry[mid] = Monster(monster_id=mid, species=species, current_hp=100)
        result = three_monster_team.get_team_monsters(registry)
        assert len(result) == 3
        assert [m.monster_id for m in result] == ["m1", "m2", "m3"]

    def test_skips_missing_monsters(
        self, three_monster_team: Team, species: MonsterSpecies
    ) -> None:
        registry = {
            "m1": Monster(monster_id="m1", species=species, current_hp=100),
        }
        result = three_monster_team.get_team_monsters(registry)
        assert len(result) == 1
        assert result[0].monster_id == "m1"

    def test_empty_team_returns_empty(self, empty_team: Team) -> None:
        assert empty_team.get_team_monsters({}) == []


# ---------------------------------------------------------------------------
# Full composition scenario
# ---------------------------------------------------------------------------


class TestFullComposition:
    def test_team_with_all_roles(self) -> None:
        """Build a full 6-monster team with suggested composition roles."""
        team = Team(team_id="comp_team", name="Full Comp")
        roles = [
            ("tank_1", TeamRole.TANK),
            ("dps_1", TeamRole.DPS),
            ("dps_2", TeamRole.DPS),
            ("support_1", TeamRole.SUPPORT),
            ("flex_1", TeamRole.FLEX),
            ("off_tank_1", TeamRole.OFF_TANK),
        ]
        for mid, role in roles:
            assert team.add_monster(mid, role=role) is True

        assert team.is_full is True
        assert team.size == MAX_TEAM_SIZE
        assert team.get_monsters_by_role(TeamRole.TANK) == ["tank_1"]
        assert team.get_monsters_by_role(TeamRole.DPS) == ["dps_1", "dps_2"]
        assert team.get_monsters_by_role(TeamRole.SUPPORT) == ["support_1"]
        assert team.get_monsters_by_role(TeamRole.FLEX) == ["flex_1"]
        assert team.get_monsters_by_role(TeamRole.OFF_TANK) == ["off_tank_1"]
