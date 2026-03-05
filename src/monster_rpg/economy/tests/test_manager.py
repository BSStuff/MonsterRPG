"""Tests for economy manager — Area model, CurrencyTransaction, EconomyManager."""

import pytest
from pydantic import ValidationError

from monster_rpg.economy.manager import (
    Area,
    AreaDifficulty,
    CurrencyTransaction,
    EconomyManager,
)


def _make_area(**overrides: object) -> Area:
    """Create an Area with sensible defaults."""
    defaults: dict[str, object] = {
        "area_id": "area_forest",
        "name": "Verdant Forest",
        "difficulty": AreaDifficulty.EASY,
        "recommended_level": 5,
        "description": "A lush forest teeming with low-level monsters.",
    }
    defaults.update(overrides)
    return Area(**defaults)


class TestAreaDifficulty:
    """Tests for AreaDifficulty enum."""

    def test_all_difficulties(self) -> None:
        """All four difficulties should be defined."""
        assert set(AreaDifficulty) == {
            AreaDifficulty.EASY,
            AreaDifficulty.MEDIUM,
            AreaDifficulty.HARD,
            AreaDifficulty.BOSS,
        }

    def test_values(self) -> None:
        """Difficulty values should be lowercase strings."""
        assert AreaDifficulty.EASY.value == "easy"
        assert AreaDifficulty.BOSS.value == "boss"


class TestArea:
    """Tests for Area model."""

    def test_valid_construction(self) -> None:
        """Area should accept valid data."""
        area = _make_area()
        assert area.area_id == "area_forest"
        assert area.name == "Verdant Forest"
        assert area.difficulty == AreaDifficulty.EASY
        assert area.recommended_level == 5

    def test_empty_area_id_rejected(self) -> None:
        """area_id cannot be empty."""
        with pytest.raises(ValidationError):
            _make_area(area_id="")

    def test_defaults(self) -> None:
        """Lists should default to empty."""
        area = _make_area()
        assert area.monster_species_ids == []
        assert area.material_drop_ids == []

    def test_with_monsters_and_materials(self) -> None:
        """Area should accept monster and material IDs."""
        area = _make_area(
            monster_species_ids=["sp_1", "sp_2"],
            material_drop_ids=["mat_wood", "mat_stone"],
        )
        assert len(area.monster_species_ids) == 2
        assert len(area.material_drop_ids) == 2

    def test_empty_name_rejected(self) -> None:
        """Name cannot be empty."""
        with pytest.raises(ValidationError):
            _make_area(name="")

    def test_long_name_rejected(self) -> None:
        """Name cannot exceed 50 characters."""
        with pytest.raises(ValidationError):
            _make_area(name="B" * 51)

    def test_recommended_level_bounds(self) -> None:
        """Recommended level must be between 1 and 100."""
        with pytest.raises(ValidationError):
            _make_area(recommended_level=0)
        with pytest.raises(ValidationError):
            _make_area(recommended_level=101)


# --- CurrencyTransaction Tests ---


class TestCurrencyTransaction:
    """Tests for CurrencyTransaction model."""

    def test_valid_gold_transaction(self) -> None:
        txn = CurrencyTransaction(
            transaction_id="gold_0",
            currency_type="gold",
            amount=-100,
            reason="Bought potion",
            balance_after=900,
        )
        assert txn.currency_type == "gold"
        assert txn.amount == -100
        assert txn.balance_after == 900

    def test_valid_gems_transaction(self) -> None:
        txn = CurrencyTransaction(
            transaction_id="gems_0",
            currency_type="gems",
            amount=50,
            reason="Daily reward",
            balance_after=150,
        )
        assert txn.currency_type == "gems"

    def test_invalid_currency_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CurrencyTransaction(
                transaction_id="bad_0",
                currency_type="coins",
                amount=10,
                reason="test",
                balance_after=10,
            )

    def test_empty_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CurrencyTransaction(
                transaction_id="gold_0",
                currency_type="gold",
                amount=10,
                reason="",
                balance_after=10,
            )

    def test_negative_balance_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CurrencyTransaction(
                transaction_id="gold_0",
                currency_type="gold",
                amount=-100,
                reason="overspend",
                balance_after=-1,
            )


# --- EconomyManager Tests ---


class TestEconomyManager:
    """Tests for EconomyManager."""

    def test_construction(self) -> None:
        mgr = EconomyManager()
        assert mgr.transaction_log == []

    def test_spend_gold_success(self) -> None:
        mgr = EconomyManager()
        success, balance = mgr.spend_gold(1000, 200, "Buy sword")
        assert success is True
        assert balance == 800

    def test_spend_gold_insufficient(self) -> None:
        mgr = EconomyManager()
        success, balance = mgr.spend_gold(50, 200, "Buy sword")
        assert success is False
        assert balance == 50

    def test_spend_gold_exact_amount(self) -> None:
        mgr = EconomyManager()
        success, balance = mgr.spend_gold(100, 100, "Exact purchase")
        assert success is True
        assert balance == 0

    def test_spend_gold_zero_raises(self) -> None:
        mgr = EconomyManager()
        with pytest.raises(ValueError, match="positive"):
            mgr.spend_gold(100, 0, "bad")

    def test_spend_gold_negative_raises(self) -> None:
        mgr = EconomyManager()
        with pytest.raises(ValueError, match="positive"):
            mgr.spend_gold(100, -5, "bad")

    def test_earn_gold(self) -> None:
        mgr = EconomyManager()
        new_balance = mgr.earn_gold(500, 150, "Monster drop")
        assert new_balance == 650

    def test_earn_gold_zero_raises(self) -> None:
        mgr = EconomyManager()
        with pytest.raises(ValueError, match="positive"):
            mgr.earn_gold(100, 0, "bad")

    def test_spend_gems_success(self) -> None:
        mgr = EconomyManager()
        success, balance = mgr.spend_gems(100, 30, "Queue slot")
        assert success is True
        assert balance == 70

    def test_spend_gems_insufficient(self) -> None:
        mgr = EconomyManager()
        success, balance = mgr.spend_gems(10, 50, "Queue slot")
        assert success is False
        assert balance == 10

    def test_spend_gems_zero_raises(self) -> None:
        mgr = EconomyManager()
        with pytest.raises(ValueError, match="positive"):
            mgr.spend_gems(100, 0, "bad")

    def test_earn_gems(self) -> None:
        mgr = EconomyManager()
        new_balance = mgr.earn_gems(50, 25, "Daily login")
        assert new_balance == 75

    def test_earn_gems_zero_raises(self) -> None:
        mgr = EconomyManager()
        with pytest.raises(ValueError, match="positive"):
            mgr.earn_gems(50, 0, "bad")

    def test_transaction_log_records(self) -> None:
        mgr = EconomyManager()
        mgr.earn_gold(0, 500, "Starting gold")
        mgr.spend_gold(500, 100, "Buy potion")
        mgr.earn_gems(0, 50, "Daily reward")
        assert len(mgr.transaction_log) == 3
        assert mgr.transaction_log[0].currency_type == "gold"
        assert mgr.transaction_log[0].amount == 500
        assert mgr.transaction_log[1].amount == -100
        assert mgr.transaction_log[2].currency_type == "gems"

    def test_transaction_ids_unique(self) -> None:
        mgr = EconomyManager()
        mgr.earn_gold(0, 100, "a")
        mgr.earn_gold(100, 200, "b")
        ids = [t.transaction_id for t in mgr.transaction_log]
        assert len(ids) == len(set(ids))
