"""Unified Action Queue — manages crafting, cooking, and training actions."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from monster_rpg.config import BASE_ACTION_QUEUE_SLOTS


class ActionType(StrEnum):
    """Types of actions that can be queued."""

    CRAFT = "craft"
    COOK = "cook"
    MINE = "mine"
    TRAIN_STRATEGY = "train_strategy"
    TRAIN_SKILL = "train_skill"


class ActionStatus(StrEnum):
    """Status of a queued action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QueuedAction(BaseModel):
    """A single action in the queue."""

    action_id: str = Field(min_length=1)
    action_type: ActionType
    name: str = Field(min_length=1, max_length=100)
    duration_seconds: float = Field(gt=0)
    elapsed_seconds: float = Field(default=0.0, ge=0.0)
    status: ActionStatus = Field(default=ActionStatus.PENDING)
    # What this action produces/requires
    required_materials: dict[str, int] = Field(default_factory=dict)
    reward_xp: int = Field(default=0, ge=0)
    reward_resources: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_resource_quantities(self) -> "QueuedAction":
        """Ensure all material/resource quantities are >= 1."""
        for mat_id, qty in self.required_materials.items():
            if qty < 1:
                raise ValueError(f"Material '{mat_id}' quantity must be >= 1, got {qty}")
        for res_id, qty in self.reward_resources.items():
            if qty < 1:
                raise ValueError(f"Resource '{res_id}' quantity must be >= 1, got {qty}")
        return self

    @property
    def is_complete(self) -> bool:
        """Check if action has finished."""
        return self.elapsed_seconds >= self.duration_seconds

    @property
    def progress_percent(self) -> float:
        """Get completion percentage (0.0 to 1.0)."""
        if self.duration_seconds <= 0:
            return 1.0
        return min(self.elapsed_seconds / self.duration_seconds, 1.0)

    def advance(self, seconds: float) -> bool:
        """Advance the action by given seconds.

        Returns:
            True if the action completed during this advance.
        """
        if self.status != ActionStatus.IN_PROGRESS:
            return False
        was_complete = self.is_complete
        self.elapsed_seconds = min(self.elapsed_seconds + seconds, self.duration_seconds)
        if not was_complete and self.is_complete:
            self.status = ActionStatus.COMPLETED
            return True
        return False


class ActionQueue(BaseModel):
    """Player's unified action queue.

    Supports multiple slots for parallel actions.
    Base 2 slots, expandable via premium currency.
    """

    max_slots: int = Field(default=BASE_ACTION_QUEUE_SLOTS, ge=1, le=8)
    actions: list[QueuedAction] = Field(default_factory=list)

    @property
    def active_count(self) -> int:
        """Count of active (non-completed, non-cancelled) actions."""
        return len(
            [
                a
                for a in self.actions
                if a.status in (ActionStatus.PENDING, ActionStatus.IN_PROGRESS)
            ]
        )

    @property
    def has_free_slot(self) -> bool:
        """Check if there's a free slot for a new action."""
        return self.active_count < self.max_slots

    def add_action(self, action: QueuedAction) -> bool:
        """Add an action to the queue.

        Returns:
            True if added, False if no free slots.
        """
        if not self.has_free_slot:
            return False
        self.actions.append(action)
        # Auto-start if it's the only pending action or there's capacity
        if action.status == ActionStatus.PENDING:
            action.status = ActionStatus.IN_PROGRESS
        return True

    def cancel_action(self, action_id: str) -> bool:
        """Cancel a queued action.

        Returns:
            True if cancelled, False if not found or already complete.
        """
        for action in self.actions:
            if action.action_id == action_id and action.status in (
                ActionStatus.PENDING,
                ActionStatus.IN_PROGRESS,
            ):
                action.status = ActionStatus.CANCELLED
                return True
        return False

    def advance_all(self, seconds: float) -> list[QueuedAction]:
        """Advance all in-progress actions by given seconds.

        Returns:
            List of actions that completed during this advance.
        """
        completed: list[QueuedAction] = []
        for action in self.actions:
            if action.advance(seconds):
                completed.append(action)
        return completed

    def clear_completed(self) -> list[QueuedAction]:
        """Remove and return all completed/cancelled actions."""
        finished = [
            a for a in self.actions if a.status in (ActionStatus.COMPLETED, ActionStatus.CANCELLED)
        ]
        self.actions = [
            a
            for a in self.actions
            if a.status not in (ActionStatus.COMPLETED, ActionStatus.CANCELLED)
        ]
        return finished

    def expand_slots(self, additional: int = 1) -> int:
        """Add more queue slots (via premium purchase).

        Returns:
            New max_slots value.

        Raises:
            ValueError: If additional is not positive.
        """
        if additional <= 0:
            raise ValueError("Additional slots must be positive")
        self.max_slots = min(self.max_slots + additional, 8)
        return self.max_slots
