"""Tests for the combat service — session management, round execution, cleanup."""

from __future__ import annotations

import pytest

from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.models import Monster
from elements_rpg.services.combat_service import (
    CombatAlreadyFinishedError,
    CombatSessionNotFoundError,
    TooManySessionsError,
    _active_sessions,
    _create_enemy_monster,
    clear_all_sessions,
    execute_round,
    finish_combat,
    get_combat_log,
    get_combat_state,
    start_combat,
)

PLAYER_ID = "test-player-001"
ENEMY_SPECIES = "species_leaflet"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _cleanup_sessions():
    """Clear all sessions before and after each test."""
    clear_all_sessions()
    yield
    clear_all_sessions()


def _make_player_team(count: int = 2) -> list[Monster]:
    """Build a small player team from the bestiary for testing."""
    species_list = list(MVP_SPECIES.values())[:count]
    team: list[Monster] = []
    for i, species in enumerate(species_list):
        monster = Monster(
            monster_id=f"player_mon_{i}",
            species=species,
            level=10,
            experience=0,
            bond_level=0,
            equipped_skill_ids=species.learnable_skill_ids[:2],
            current_hp=species.base_stats.hp,
            is_fainted=False,
        )
        monster.current_hp = monster.max_hp()
        team.append(monster)
    return team


# ===================================================================
# 1. Enemy Monster Creation
# ===================================================================


class TestCreateEnemyMonster:
    """Tests for _create_enemy_monster helper."""

    def test_creates_valid_monster(self) -> None:
        """Should create a monster from a valid species ID."""
        monster = _create_enemy_monster(ENEMY_SPECIES, level=5)
        assert monster.species.species_id == ENEMY_SPECIES
        assert monster.level == 5
        assert not monster.is_fainted
        assert monster.current_hp == monster.max_hp()
        assert len(monster.equipped_skill_ids) >= 1

    def test_invalid_species_raises(self) -> None:
        """Should raise ValueError for unknown species."""
        with pytest.raises(ValueError, match="Unknown species"):
            _create_enemy_monster("nonexistent_species")

    def test_monster_id_starts_with_enemy(self) -> None:
        """Enemy monsters should have IDs prefixed with 'enemy_'."""
        monster = _create_enemy_monster(ENEMY_SPECIES)
        assert monster.monster_id.startswith("enemy_")


# ===================================================================
# 2. Start Combat
# ===================================================================


class TestStartCombat:
    """Tests for start_combat."""

    @pytest.mark.asyncio
    async def test_start_combat_success(self) -> None:
        """Should create a session and return session_id + initial state."""
        result = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        assert "session_id" in result
        assert "state" in result
        state = result["state"]
        assert state["round"] == 0
        assert state["is_finished"] is False
        assert state["player_won"] is None
        assert len(state["player_team"]) == 2
        assert len(state["enemy_team"]) == 1

    @pytest.mark.asyncio
    async def test_start_combat_empty_player_team_raises(self) -> None:
        """Should reject empty player teams."""
        with pytest.raises(ValueError, match="empty player team"):
            await start_combat(
                player_id=PLAYER_ID,
                player_monsters=[],
                enemy_species_ids=[ENEMY_SPECIES],
            )

    @pytest.mark.asyncio
    async def test_start_combat_empty_enemies_raises(self) -> None:
        """Should reject empty enemy species list."""
        with pytest.raises(ValueError, match="at least one enemy"):
            await start_combat(
                player_id=PLAYER_ID,
                player_monsters=_make_player_team(),
                enemy_species_ids=[],
            )

    @pytest.mark.asyncio
    async def test_start_combat_invalid_species_raises(self) -> None:
        """Should raise ValueError for invalid enemy species."""
        with pytest.raises(ValueError, match="Unknown species"):
            await start_combat(
                player_id=PLAYER_ID,
                player_monsters=_make_player_team(),
                enemy_species_ids=["fake_species"],
            )

    @pytest.mark.asyncio
    async def test_start_combat_too_many_sessions_raises(self) -> None:
        """Should reject when player hits session limit."""
        for _ in range(3):
            await start_combat(
                player_id=PLAYER_ID,
                player_monsters=_make_player_team(),
                enemy_species_ids=[ENEMY_SPECIES],
            )
        with pytest.raises(TooManySessionsError, match="already has"):
            await start_combat(
                player_id=PLAYER_ID,
                player_monsters=_make_player_team(),
                enemy_species_ids=[ENEMY_SPECIES],
            )

    @pytest.mark.asyncio
    async def test_start_combat_with_enemy_level(self) -> None:
        """Should create enemies at the specified level."""
        result = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
            enemy_level=15,
        )
        enemy = result["state"]["enemy_team"][0]
        assert enemy["level"] == 15

    @pytest.mark.asyncio
    async def test_different_players_can_have_sessions(self) -> None:
        """Different players should have independent session limits."""
        for _ in range(3):
            await start_combat(
                player_id="player-A",
                player_monsters=_make_player_team(),
                enemy_species_ids=[ENEMY_SPECIES],
            )
        # Different player should succeed
        result = await start_combat(
            player_id="player-B",
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        assert "session_id" in result


# ===================================================================
# 3. Execute Round
# ===================================================================


class TestExecuteRound:
    """Tests for execute_round."""

    @pytest.mark.asyncio
    async def test_execute_round_success(self) -> None:
        """Should execute a round and return results."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        result = await execute_round(session_id, PLAYER_ID)

        assert "round_result" in result
        assert "state" in result
        assert result["state"]["round"] == 1
        assert result["round_result"]["round_number"] == 1

    @pytest.mark.asyncio
    async def test_execute_round_not_found(self) -> None:
        """Should raise for unknown session."""
        with pytest.raises(CombatSessionNotFoundError):
            await execute_round("nonexistent-id", PLAYER_ID)

    @pytest.mark.asyncio
    async def test_execute_round_wrong_player(self) -> None:
        """Should reject if session belongs to another player."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        with pytest.raises(CombatSessionNotFoundError):
            await execute_round(session_id, "wrong-player")

    @pytest.mark.asyncio
    async def test_execute_round_already_finished(self) -> None:
        """Should raise CombatAlreadyFinishedError if combat is over."""
        # Create a combat with very weak enemy (level 1) vs strong player (level 10)
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
            enemy_level=1,
        )
        session_id = start["session_id"]

        # Run rounds until combat finishes
        for _ in range(100):
            result = await execute_round(session_id, PLAYER_ID)
            if result["state"]["is_finished"]:
                break

        # Next round should raise
        with pytest.raises(CombatAlreadyFinishedError):
            await execute_round(session_id, PLAYER_ID)

    @pytest.mark.asyncio
    async def test_multiple_rounds_increment(self) -> None:
        """Round counter should increment with each call."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES, ENEMY_SPECIES, ENEMY_SPECIES],
            enemy_level=50,
        )
        session_id = start["session_id"]

        r1 = await execute_round(session_id, PLAYER_ID)
        r2 = await execute_round(session_id, PLAYER_ID)

        assert r1["state"]["round"] == 1
        assert r2["state"]["round"] == 2


# ===================================================================
# 4. Finish Combat
# ===================================================================


class TestFinishCombat:
    """Tests for finish_combat."""

    @pytest.mark.asyncio
    async def test_finish_combat_success(self) -> None:
        """Should return final results and remove session."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]

        # Execute a round first
        await execute_round(session_id, PLAYER_ID)

        result = await finish_combat(session_id, PLAYER_ID)
        assert "finished" in result
        assert "player_won" in result
        assert "rounds" in result
        assert "log" in result
        assert result["rounds"] == 1

        # Session should be removed
        assert session_id not in _active_sessions

    @pytest.mark.asyncio
    async def test_finish_combat_not_found(self) -> None:
        """Should raise for unknown session."""
        with pytest.raises(CombatSessionNotFoundError):
            await finish_combat("nonexistent-id", PLAYER_ID)

    @pytest.mark.asyncio
    async def test_finish_combat_wrong_player(self) -> None:
        """Should reject if session belongs to another player."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        with pytest.raises(CombatSessionNotFoundError):
            await finish_combat(session_id, "wrong-player")

    @pytest.mark.asyncio
    async def test_finish_combat_double_finish_raises(self) -> None:
        """Finishing same session twice should raise."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        await finish_combat(session_id, PLAYER_ID)

        with pytest.raises(CombatSessionNotFoundError):
            await finish_combat(session_id, PLAYER_ID)


# ===================================================================
# 5. Get Combat State
# ===================================================================


class TestGetCombatState:
    """Tests for get_combat_state."""

    @pytest.mark.asyncio
    async def test_get_state_success(self) -> None:
        """Should return current state snapshot."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        state = await get_combat_state(session_id, PLAYER_ID)

        assert state["session_id"] == session_id
        assert state["player_id"] == PLAYER_ID
        assert state["round"] == 0
        assert len(state["player_team"]) > 0
        assert len(state["enemy_team"]) > 0

    @pytest.mark.asyncio
    async def test_get_state_not_found(self) -> None:
        """Should raise for unknown session."""
        with pytest.raises(CombatSessionNotFoundError):
            await get_combat_state("nonexistent-id", PLAYER_ID)


# ===================================================================
# 6. Get Combat Log
# ===================================================================


class TestGetCombatLog:
    """Tests for get_combat_log."""

    @pytest.mark.asyncio
    async def test_get_log_empty(self) -> None:
        """Log should be empty before any rounds are executed."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        session_id = start["session_id"]
        log = await get_combat_log(session_id, PLAYER_ID)

        assert log["session_id"] == session_id
        assert log["rounds"] == 0
        assert log["log"] == []

    @pytest.mark.asyncio
    async def test_get_log_after_rounds(self) -> None:
        """Log should contain entries after rounds are executed."""
        start = await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES, ENEMY_SPECIES],
            enemy_level=50,
        )
        session_id = start["session_id"]

        await execute_round(session_id, PLAYER_ID)
        await execute_round(session_id, PLAYER_ID)

        log = await get_combat_log(session_id, PLAYER_ID)
        assert log["rounds"] == 2
        assert len(log["log"]) == 2

    @pytest.mark.asyncio
    async def test_get_log_not_found(self) -> None:
        """Should raise for unknown session."""
        with pytest.raises(CombatSessionNotFoundError):
            await get_combat_log("nonexistent-id", PLAYER_ID)


# ===================================================================
# 7. Clear Sessions
# ===================================================================


class TestClearSessions:
    """Tests for clear_all_sessions."""

    @pytest.mark.asyncio
    async def test_clear_removes_all(self) -> None:
        """clear_all_sessions should empty the session store."""
        await start_combat(
            player_id=PLAYER_ID,
            player_monsters=_make_player_team(),
            enemy_species_ids=[ENEMY_SPECIES],
        )
        assert len(_active_sessions) == 1
        clear_all_sessions()
        assert len(_active_sessions) == 0
