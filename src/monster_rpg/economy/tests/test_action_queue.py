"""Tests for the Unified Action Queue system."""

import pytest

from monster_rpg.config import BASE_ACTION_QUEUE_SLOTS
from monster_rpg.economy.action_queue import (
    ActionQueue,
    ActionStatus,
    ActionType,
    QueuedAction,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def craft_action() -> QueuedAction:
    """A simple crafting action."""
    return QueuedAction(
        action_id="craft_sword_1",
        action_type=ActionType.CRAFT,
        name="Craft Iron Sword",
        duration_seconds=60.0,
        required_materials={"iron_ore": 3, "wood": 1},
        reward_xp=25,
        reward_resources={"iron_sword": 1},
    )


@pytest.fixture
def cook_action() -> QueuedAction:
    """A simple cooking action."""
    return QueuedAction(
        action_id="cook_steak_1",
        action_type=ActionType.COOK,
        name="Cook Monster Steak",
        duration_seconds=30.0,
        reward_xp=15,
        reward_resources={"monster_steak": 1},
    )


@pytest.fixture
def train_action() -> QueuedAction:
    """A strategy training action."""
    return QueuedAction(
        action_id="train_strat_1",
        action_type=ActionType.TRAIN_STRATEGY,
        name="Train Defensive Strategy",
        duration_seconds=120.0,
        reward_xp=50,
    )


@pytest.fixture
def queue() -> ActionQueue:
    """An empty action queue with default slots."""
    return ActionQueue()


# ---------------------------------------------------------------------------
# QueuedAction — Construction & Defaults
# ---------------------------------------------------------------------------


class TestQueuedActionConstruction:
    """Tests for QueuedAction model creation and defaults."""

    def test_construction_with_defaults(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Test",
            duration_seconds=10.0,
        )
        assert action.elapsed_seconds == 0.0
        assert action.status == ActionStatus.PENDING
        assert action.required_materials == {}
        assert action.reward_xp == 0
        assert action.reward_resources == {}

    def test_construction_with_all_fields(self) -> None:
        action = QueuedAction(
            action_id="a2",
            action_type=ActionType.COOK,
            name="Full Action",
            duration_seconds=45.0,
            elapsed_seconds=10.0,
            status=ActionStatus.IN_PROGRESS,
            required_materials={"meat": 2},
            reward_xp=30,
            reward_resources={"steak": 1},
        )
        assert action.action_type == ActionType.COOK
        assert action.elapsed_seconds == 10.0
        assert action.status == ActionStatus.IN_PROGRESS
        assert action.reward_xp == 30

    def test_action_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            QueuedAction(
                action_id="",
                action_type=ActionType.MINE,
                name="Bad",
                duration_seconds=5.0,
            )

    def test_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            QueuedAction(
                action_id="a1",
                action_type=ActionType.MINE,
                name="",
                duration_seconds=5.0,
            )

    def test_duration_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            QueuedAction(
                action_id="a1",
                action_type=ActionType.MINE,
                name="Bad",
                duration_seconds=0.0,
            )

    def test_queued_action_zero_material_raises(self) -> None:
        with pytest.raises(ValueError, match="quantity must be >= 1"):
            QueuedAction(
                action_id="a1",
                action_type=ActionType.CRAFT,
                name="Bad",
                duration_seconds=10.0,
                required_materials={"iron": 0},
            )

    def test_queued_action_zero_reward_resource_raises(self) -> None:
        with pytest.raises(ValueError, match="quantity must be >= 1"):
            QueuedAction(
                action_id="a1",
                action_type=ActionType.CRAFT,
                name="Bad",
                duration_seconds=10.0,
                reward_resources={"sword": 0},
            )


# ---------------------------------------------------------------------------
# QueuedAction — Properties
# ---------------------------------------------------------------------------


class TestQueuedActionProperties:
    """Tests for is_complete and progress_percent."""

    def test_is_complete_false_at_start(self, craft_action: QueuedAction) -> None:
        assert craft_action.is_complete is False

    def test_is_complete_true_when_elapsed_equals_duration(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Done",
            duration_seconds=10.0,
            elapsed_seconds=10.0,
        )
        assert action.is_complete is True

    def test_is_complete_true_when_elapsed_exceeds_duration(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Over",
            duration_seconds=10.0,
            elapsed_seconds=15.0,
        )
        assert action.is_complete is True

    def test_progress_percent_zero(self, craft_action: QueuedAction) -> None:
        assert craft_action.progress_percent == pytest.approx(0.0)

    def test_progress_percent_fifty(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Half",
            duration_seconds=100.0,
            elapsed_seconds=50.0,
        )
        assert action.progress_percent == pytest.approx(0.5)

    def test_progress_percent_hundred(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Full",
            duration_seconds=100.0,
            elapsed_seconds=100.0,
        )
        assert action.progress_percent == pytest.approx(1.0)

    def test_progress_percent_clamped_at_one(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.CRAFT,
            name="Over",
            duration_seconds=10.0,
            elapsed_seconds=20.0,
        )
        assert action.progress_percent == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# QueuedAction — advance()
# ---------------------------------------------------------------------------


class TestQueuedActionAdvance:
    """Tests for the advance() method."""

    def test_advance_increments_elapsed(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.MINE,
            name="Mining",
            duration_seconds=60.0,
            status=ActionStatus.IN_PROGRESS,
        )
        result = action.advance(10.0)
        assert result is False
        assert action.elapsed_seconds == pytest.approx(10.0)
        assert action.status == ActionStatus.IN_PROGRESS

    def test_advance_completes_action(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.MINE,
            name="Mining",
            duration_seconds=20.0,
            elapsed_seconds=15.0,
            status=ActionStatus.IN_PROGRESS,
        )
        result = action.advance(10.0)
        assert result is True
        assert action.status == ActionStatus.COMPLETED

    def test_advance_does_nothing_if_pending(self, craft_action: QueuedAction) -> None:
        assert craft_action.status == ActionStatus.PENDING
        result = craft_action.advance(10.0)
        assert result is False
        assert craft_action.elapsed_seconds == 0.0

    def test_advance_does_nothing_if_completed(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.COOK,
            name="Done",
            duration_seconds=10.0,
            elapsed_seconds=10.0,
            status=ActionStatus.COMPLETED,
        )
        result = action.advance(5.0)
        assert result is False

    def test_advance_does_nothing_if_cancelled(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.COOK,
            name="Cancelled",
            duration_seconds=10.0,
            status=ActionStatus.CANCELLED,
        )
        result = action.advance(5.0)
        assert result is False
        assert action.elapsed_seconds == 0.0

    def test_advance_clamps_to_duration(self) -> None:
        action = QueuedAction(
            action_id="a1",
            action_type=ActionType.TRAIN_SKILL,
            name="Train",
            duration_seconds=10.0,
            status=ActionStatus.IN_PROGRESS,
        )
        action.advance(100.0)
        assert action.elapsed_seconds == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# ActionQueue — Construction
# ---------------------------------------------------------------------------


class TestActionQueueConstruction:
    """Tests for ActionQueue model creation."""

    def test_default_slots(self, queue: ActionQueue) -> None:
        assert queue.max_slots == BASE_ACTION_QUEUE_SLOTS
        assert queue.max_slots == 2

    def test_empty_actions(self, queue: ActionQueue) -> None:
        assert queue.actions == []
        assert queue.active_count == 0

    def test_has_free_slot_when_empty(self, queue: ActionQueue) -> None:
        assert queue.has_free_slot is True


# ---------------------------------------------------------------------------
# ActionQueue — add_action
# ---------------------------------------------------------------------------


class TestActionQueueAdd:
    """Tests for adding actions to the queue."""

    def test_add_action_succeeds(self, queue: ActionQueue, craft_action: QueuedAction) -> None:
        result = queue.add_action(craft_action)
        assert result is True
        assert len(queue.actions) == 1

    def test_add_action_auto_starts(self, queue: ActionQueue, craft_action: QueuedAction) -> None:
        queue.add_action(craft_action)
        assert craft_action.status == ActionStatus.IN_PROGRESS

    def test_add_two_actions_both_start(
        self,
        queue: ActionQueue,
        craft_action: QueuedAction,
        cook_action: QueuedAction,
    ) -> None:
        queue.add_action(craft_action)
        queue.add_action(cook_action)
        assert craft_action.status == ActionStatus.IN_PROGRESS
        assert cook_action.status == ActionStatus.IN_PROGRESS
        assert queue.active_count == 2

    def test_add_action_fails_when_full(
        self,
        queue: ActionQueue,
        craft_action: QueuedAction,
        cook_action: QueuedAction,
        train_action: QueuedAction,
    ) -> None:
        queue.add_action(craft_action)
        queue.add_action(cook_action)
        result = queue.add_action(train_action)
        assert result is False
        assert len(queue.actions) == 2
        assert train_action.status == ActionStatus.PENDING  # unchanged


# ---------------------------------------------------------------------------
# ActionQueue — cancel_action
# ---------------------------------------------------------------------------


class TestActionQueueCancel:
    """Tests for cancelling queued actions."""

    def test_cancel_in_progress_action(
        self, queue: ActionQueue, craft_action: QueuedAction
    ) -> None:
        queue.add_action(craft_action)
        result = queue.cancel_action("craft_sword_1")
        assert result is True
        assert craft_action.status == ActionStatus.CANCELLED

    def test_cancel_frees_slot(self, queue: ActionQueue, craft_action: QueuedAction) -> None:
        queue.add_action(craft_action)
        queue.cancel_action("craft_sword_1")
        assert queue.active_count == 0
        assert queue.has_free_slot is True

    def test_cancel_returns_false_for_completed(self, queue: ActionQueue) -> None:
        action = QueuedAction(
            action_id="done_1",
            action_type=ActionType.COOK,
            name="Done",
            duration_seconds=10.0,
            elapsed_seconds=10.0,
            status=ActionStatus.COMPLETED,
        )
        queue.actions.append(action)
        result = queue.cancel_action("done_1")
        assert result is False

    def test_cancel_returns_false_for_unknown_id(self, queue: ActionQueue) -> None:
        result = queue.cancel_action("nonexistent_id")
        assert result is False


# ---------------------------------------------------------------------------
# ActionQueue — advance_all
# ---------------------------------------------------------------------------


class TestActionQueueAdvance:
    """Tests for advancing all actions."""

    def test_advance_all_progresses_actions(
        self,
        queue: ActionQueue,
        craft_action: QueuedAction,
        cook_action: QueuedAction,
    ) -> None:
        queue.add_action(craft_action)
        queue.add_action(cook_action)
        completed = queue.advance_all(10.0)
        assert completed == []
        assert craft_action.elapsed_seconds == pytest.approx(10.0)
        assert cook_action.elapsed_seconds == pytest.approx(10.0)

    def test_advance_all_returns_completed(
        self, queue: ActionQueue, cook_action: QueuedAction
    ) -> None:
        queue.add_action(cook_action)  # 30s duration
        completed = queue.advance_all(30.0)
        assert len(completed) == 1
        assert completed[0].action_id == "cook_steak_1"
        assert completed[0].status == ActionStatus.COMPLETED

    def test_advance_all_mixed_completion(
        self,
        queue: ActionQueue,
        craft_action: QueuedAction,
        cook_action: QueuedAction,
    ) -> None:
        queue.add_action(craft_action)  # 60s
        queue.add_action(cook_action)  # 30s
        completed = queue.advance_all(30.0)
        assert len(completed) == 1
        assert completed[0].action_id == "cook_steak_1"
        assert craft_action.status == ActionStatus.IN_PROGRESS
        assert craft_action.elapsed_seconds == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# ActionQueue — clear_completed
# ---------------------------------------------------------------------------


class TestActionQueueClear:
    """Tests for clearing completed/cancelled actions."""

    def test_clear_completed_removes_finished(
        self, queue: ActionQueue, cook_action: QueuedAction
    ) -> None:
        queue.add_action(cook_action)
        queue.advance_all(30.0)  # completes cook_action
        cleared = queue.clear_completed()
        assert len(cleared) == 1
        assert cleared[0].action_id == "cook_steak_1"
        assert len(queue.actions) == 0

    def test_clear_completed_removes_cancelled(
        self, queue: ActionQueue, craft_action: QueuedAction
    ) -> None:
        queue.add_action(craft_action)
        queue.cancel_action("craft_sword_1")
        cleared = queue.clear_completed()
        assert len(cleared) == 1
        assert cleared[0].status == ActionStatus.CANCELLED
        assert len(queue.actions) == 0

    def test_clear_completed_keeps_in_progress(
        self,
        queue: ActionQueue,
        craft_action: QueuedAction,
        cook_action: QueuedAction,
    ) -> None:
        queue.add_action(craft_action)  # 60s
        queue.add_action(cook_action)  # 30s
        queue.advance_all(30.0)
        cleared = queue.clear_completed()
        assert len(cleared) == 1  # only cook
        assert len(queue.actions) == 1  # craft remains
        assert queue.actions[0].action_id == "craft_sword_1"


# ---------------------------------------------------------------------------
# ActionQueue — expand_slots
# ---------------------------------------------------------------------------


class TestActionQueueExpand:
    """Tests for expanding queue slots."""

    def test_expand_slots_increases_max(self, queue: ActionQueue) -> None:
        new_max = queue.expand_slots(1)
        assert new_max == 3
        assert queue.max_slots == 3

    def test_expand_slots_caps_at_8(self, queue: ActionQueue) -> None:
        new_max = queue.expand_slots(100)
        assert new_max == 8
        assert queue.max_slots == 8

    def test_expand_slots_zero_raises(self, queue: ActionQueue) -> None:
        with pytest.raises(ValueError, match="positive"):
            queue.expand_slots(0)

    def test_expand_slots_negative_raises(self, queue: ActionQueue) -> None:
        with pytest.raises(ValueError, match="positive"):
            queue.expand_slots(-3)

    def test_expand_slots_allows_more_actions(self, queue: ActionQueue) -> None:
        queue.expand_slots(2)  # now 4 slots
        for i in range(4):
            action = QueuedAction(
                action_id=f"action_{i}",
                action_type=ActionType.MINE,
                name=f"Mine {i}",
                duration_seconds=10.0,
            )
            assert queue.add_action(action) is True
        assert queue.active_count == 4
        assert queue.has_free_slot is False


# ---------------------------------------------------------------------------
# ActionQueue — active_count
# ---------------------------------------------------------------------------


class TestActionQueueActiveCount:
    """Tests for active_count property."""

    def test_active_count_zero_when_empty(self, queue: ActionQueue) -> None:
        assert queue.active_count == 0

    def test_active_count_reflects_in_progress(
        self, queue: ActionQueue, craft_action: QueuedAction
    ) -> None:
        queue.add_action(craft_action)
        assert queue.active_count == 1

    def test_active_count_excludes_completed(
        self, queue: ActionQueue, cook_action: QueuedAction
    ) -> None:
        queue.add_action(cook_action)
        queue.advance_all(30.0)
        assert queue.active_count == 0

    def test_active_count_excludes_cancelled(
        self, queue: ActionQueue, craft_action: QueuedAction
    ) -> None:
        queue.add_action(craft_action)
        queue.cancel_action("craft_sword_1")
        assert queue.active_count == 0
