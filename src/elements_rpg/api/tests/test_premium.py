"""Integration tests for the premium router endpoints.

Covers gem packages, upgrades, subscriptions, and reward ads.
All external dependencies (auth, DB, services) are mocked.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.config import Settings, get_settings
from elements_rpg.db.session import get_db
from elements_rpg.economy.premium import PurchaseResult

VALID_JWT_PAYLOAD: dict[str, Any] = {
    "sub": "test-player-uuid-123",
    "email": "hero@example.com",
    "role": "authenticated",
    "aud": "authenticated",
    "exp": 9999999999,
}

FAKE_PLAYER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret",
        supabase_service_key="test-service-key",
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
    )


def _create_app():
    from elements_rpg.api.app import create_app as _create

    return _create()


def _mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _mock_player() -> MagicMock:
    """Create a fake player with a deterministic UUID."""
    import uuid

    player = MagicMock()
    player.id = uuid.UUID(FAKE_PLAYER_ID)
    return player


@pytest.fixture
def app(test_settings: Settings):
    with patch("elements_rpg.api.app.get_settings", return_value=test_settings):
        application = _create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    application.dependency_overrides[get_current_user] = lambda: VALID_JWT_PAYLOAD

    mock_db = _mock_db_session()

    async def _fake_db():
        yield mock_db

    application.dependency_overrides[get_db] = _fake_db
    return application


@pytest.fixture
def unauth_app(test_settings: Settings):
    """App without auth override — endpoints requiring auth should fail."""
    with patch("elements_rpg.api.app.get_settings", return_value=test_settings):
        application = _create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings

    mock_db = _mock_db_session()

    async def _fake_db():
        yield mock_db

    application.dependency_overrides[get_db] = _fake_db
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def unauth_client(unauth_app) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=unauth_app),
        base_url="http://test",
    ) as ac:
        yield ac


# ===================================================================
# 1. GET /premium/packages — list gem packages (public)
# ===================================================================


class TestListPackages:
    """GET /premium/packages."""

    @pytest.mark.asyncio
    async def test_list_packages_success(self, client: AsyncClient) -> None:
        """Should return all gem packages."""
        response = await client.get("/premium/packages")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 5
        # Verify first package has expected fields
        pkg = body["data"][0]
        assert "package_id" in pkg
        assert "gem_amount" in pkg
        assert "price_usd" in pkg

    @pytest.mark.asyncio
    async def test_list_packages_no_auth_ok(self, unauth_client: AsyncClient) -> None:
        """Packages endpoint should work without auth."""
        response = await unauth_client.get("/premium/packages")
        assert response.status_code == 200


# ===================================================================
# 2. GET /premium/upgrades — list upgrades (public)
# ===================================================================


class TestListUpgrades:
    """GET /premium/upgrades."""

    @pytest.mark.asyncio
    async def test_list_upgrades_success(self, client: AsyncClient) -> None:
        """Should return all premium upgrades."""
        response = await client.get("/premium/upgrades")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 4
        upg = body["data"][0]
        assert "upgrade_id" in upg
        assert "gem_cost" in upg
        assert "max_purchases" in upg


# ===================================================================
# 3. POST /premium/purchase/{upgrade_id} — buy upgrade (auth)
# ===================================================================


class TestPurchaseUpgrade:
    """POST /premium/purchase/{upgrade_id}."""

    @pytest.mark.asyncio
    async def test_purchase_success(self, client: AsyncClient) -> None:
        """Should purchase upgrade and deduct gems."""
        result = PurchaseResult(success=True, gems_spent=200, gems_remaining=800)
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_purchase_upgrade",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post("/premium/purchase/upgrade_queue_slot")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["gems_spent"] == 200
        assert body["data"]["gems_remaining"] == 800

    @pytest.mark.asyncio
    async def test_purchase_insufficient_gems(self, client: AsyncClient) -> None:
        """Should return 400 when gems are insufficient."""
        result = PurchaseResult(success=False, gems_remaining=50, error="Insufficient gems")
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_purchase_upgrade",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            response = await client.post("/premium/purchase/upgrade_queue_slot")

        assert response.status_code == 400
        assert "Insufficient gems" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_purchase_invalid_upgrade(self, client: AsyncClient) -> None:
        """Should return 400 for unknown upgrade_id."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_purchase_upgrade",
                new_callable=AsyncMock,
                side_effect=ValueError("Unknown upgrade: bad_id"),
            ),
        ):
            response = await client.post("/premium/purchase/bad_id")

        assert response.status_code == 400
        assert "Unknown upgrade" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_purchase_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.post("/premium/purchase/upgrade_queue_slot")
        assert response.status_code in (401, 403)


# ===================================================================
# 4. GET /premium/purchases — purchase history (auth)
# ===================================================================


class TestGetPurchases:
    """GET /premium/purchases."""

    @pytest.mark.asyncio
    async def test_get_purchases_success(self, client: AsyncClient) -> None:
        """Should return purchase counts."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_get_purchases",
                new_callable=AsyncMock,
                return_value={"upgrade_queue_slot": 2, "upgrade_offline_cap": 1},
            ),
        ):
            response = await client.get("/premium/purchases")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["upgrade_queue_slot"] == 2

    @pytest.mark.asyncio
    async def test_get_purchases_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.get("/premium/purchases")
        assert response.status_code in (401, 403)


# ===================================================================
# 5. GET /premium/subscriptions/plans — list plans (public)
# ===================================================================


class TestListSubscriptionPlans:
    """GET /premium/subscriptions/plans."""

    @pytest.mark.asyncio
    async def test_list_plans_success(self, client: AsyncClient) -> None:
        """Should return all subscription plans."""
        response = await client.get("/premium/subscriptions/plans")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 3
        plan = body["data"][0]
        assert "plan_id" in plan
        assert "tier" in plan
        assert "benefits" in plan

    @pytest.mark.asyncio
    async def test_list_plans_no_auth_ok(self, unauth_client: AsyncClient) -> None:
        """Plans endpoint should work without auth."""
        response = await unauth_client.get("/premium/subscriptions/plans")
        assert response.status_code == 200


# ===================================================================
# 6. POST /premium/subscriptions/activate — start subscription (auth)
# ===================================================================


class TestActivateSubscription:
    """POST /premium/subscriptions/activate."""

    @pytest.mark.asyncio
    async def test_activate_success(self, client: AsyncClient) -> None:
        """Should activate a subscription plan."""
        fake_result = {
            "plan_id": "sub_monthly",
            "tier": "monthly",
            "name": "Monthly Pass",
            "start_timestamp": 1000000.0,
            "end_timestamp": 3592000.0,
            "benefits": {"ad_removal": True, "daily_gem_stipend": 50},
        }
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_activate_subscription",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.post(
                "/premium/subscriptions/activate",
                json={"plan_id": "sub_monthly"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["plan_id"] == "sub_monthly"
        assert body["data"]["tier"] == "monthly"

    @pytest.mark.asyncio
    async def test_activate_invalid_plan(self, client: AsyncClient) -> None:
        """Should return 400 for unknown plan_id."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_activate_subscription",
                new_callable=AsyncMock,
                side_effect=ValueError("Unknown subscription plan: bad_plan"),
            ),
        ):
            response = await client.post(
                "/premium/subscriptions/activate",
                json={"plan_id": "bad_plan"},
            )

        assert response.status_code == 400
        assert "Unknown subscription plan" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_activate_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.post(
            "/premium/subscriptions/activate",
            json={"plan_id": "sub_monthly"},
        )
        assert response.status_code in (401, 403)


# ===================================================================
# 7. GET /premium/subscriptions/active — get active sub (auth)
# ===================================================================


class TestGetActiveSubscription:
    """GET /premium/subscriptions/active."""

    @pytest.mark.asyncio
    async def test_active_sub_exists(self, client: AsyncClient) -> None:
        """Should return active subscription details."""
        fake_result = {
            "plan_id": "sub_monthly",
            "tier": "monthly",
            "name": "Monthly Pass",
            "start_timestamp": 1000000.0,
            "end_timestamp": 3592000.0,
            "auto_renew": True,
            "benefits": {"ad_removal": True},
        }
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_get_active_subscription",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.get("/premium/subscriptions/active")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["plan_id"] == "sub_monthly"

    @pytest.mark.asyncio
    async def test_no_active_sub(self, client: AsyncClient) -> None:
        """Should return null data when no active subscription."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_get_active_subscription",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = await client.get("/premium/subscriptions/active")

        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None

    @pytest.mark.asyncio
    async def test_active_sub_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.get("/premium/subscriptions/active")
        assert response.status_code in (401, 403)


# ===================================================================
# 8. POST /premium/subscriptions/cancel — cancel sub (auth)
# ===================================================================


class TestCancelSubscription:
    """POST /premium/subscriptions/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_success(self, client: AsyncClient) -> None:
        """Should cancel active subscription."""
        fake_result = {
            "plan_id": "sub_monthly",
            "tier": "monthly",
            "cancelled": True,
            "active_until": 3592000.0,
        }
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_cancel_subscription",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.post("/premium/subscriptions/cancel")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["cancelled"] is True

    @pytest.mark.asyncio
    async def test_cancel_no_active_sub(self, client: AsyncClient) -> None:
        """Should return 400 when no active subscription."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_cancel_subscription",
                new_callable=AsyncMock,
                side_effect=ValueError("No active subscription to cancel"),
            ),
        ):
            response = await client.post("/premium/subscriptions/cancel")

        assert response.status_code == 400
        assert "No active subscription" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.post("/premium/subscriptions/cancel")
        assert response.status_code in (401, 403)


# ===================================================================
# 9. GET /premium/ads/available — available ads (auth)
# ===================================================================


class TestGetAvailableAds:
    """GET /premium/ads/available."""

    @pytest.mark.asyncio
    async def test_available_ads_success(self, client: AsyncClient) -> None:
        """Should return ad availability for all reward types."""
        fake_result = [
            {
                "reward_type": "revive",
                "description": "Revive all fainted monsters with 50% HP",
                "available": True,
                "reason": None,
                "watches_today": 0,
                "daily_limit": 3,
            },
            {
                "reward_type": "idle_boost",
                "description": "Boost idle gains by 25%",
                "available": True,
                "reason": None,
                "watches_today": 0,
                "daily_limit": 5,
            },
        ]
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_get_available_ads",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.get("/premium/ads/available")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["data"][0]["reward_type"] == "revive"

    @pytest.mark.asyncio
    async def test_available_ads_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.get("/premium/ads/available")
        assert response.status_code in (401, 403)


# ===================================================================
# 10. POST /premium/ads/{reward_type}/watch — watch ad (auth)
# ===================================================================


class TestWatchAd:
    """POST /premium/ads/{reward_type}/watch."""

    @pytest.mark.asyncio
    async def test_watch_ad_success(self, client: AsyncClient) -> None:
        """Should record ad watch and return reward info."""
        fake_result = {
            "reward_type": "revive",
            "bonus_applied": 0.5,
            "timestamp": 1000000.0,
            "watches_today": 1,
            "daily_limit": 3,
        }
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_record_ad_watch",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.post("/premium/ads/revive/watch")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["reward_type"] == "revive"
        assert body["data"]["bonus_applied"] == 0.5

    @pytest.mark.asyncio
    async def test_watch_ad_on_cooldown(self, client: AsyncClient) -> None:
        """Should return 400 when ad is on cooldown."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_record_ad_watch",
                new_callable=AsyncMock,
                side_effect=ValueError("Cannot watch ad: Cooldown not elapsed"),
            ),
        ):
            response = await client.post("/premium/ads/revive/watch")

        assert response.status_code == 400
        assert "Cooldown" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_watch_ad_daily_limit(self, client: AsyncClient) -> None:
        """Should return 400 when daily limit reached."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_record_ad_watch",
                new_callable=AsyncMock,
                side_effect=ValueError("Cannot watch ad: Daily limit reached"),
            ),
        ):
            response = await client.post("/premium/ads/revive/watch")

        assert response.status_code == 400
        assert "Daily limit" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_watch_ad_invalid_type(self, client: AsyncClient) -> None:
        """Should return 400 for invalid reward type."""
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_record_ad_watch",
                new_callable=AsyncMock,
                side_effect=ValueError("Invalid reward type: bad_type"),
            ),
        ):
            response = await client.post("/premium/ads/bad_type/watch")

        assert response.status_code == 400
        assert "Invalid reward type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_watch_ad_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.post("/premium/ads/revive/watch")
        assert response.status_code in (401, 403)


# ===================================================================
# 11. GET /premium/ads/tracker — ad tracker (auth)
# ===================================================================


class TestGetAdTracker:
    """GET /premium/ads/tracker."""

    @pytest.mark.asyncio
    async def test_get_tracker_success(self, client: AsyncClient) -> None:
        """Should return ad tracker state."""
        fake_result = {
            "watches_today": {"revive": 1, "idle_boost": 2},
            "last_watch_time": {"revive": 1000000.0},
            "watch_history": [
                {
                    "reward_type": "revive",
                    "timestamp": 1000000.0,
                    "bonus_applied": 0.5,
                }
            ],
        }
        with (
            patch(
                "elements_rpg.api.routers.premium.get_player_by_supabase_id",
                new_callable=AsyncMock,
                return_value=_mock_player(),
            ),
            patch(
                "elements_rpg.api.routers.premium.service_get_ad_tracker",
                new_callable=AsyncMock,
                return_value=fake_result,
            ),
        ):
            response = await client.get("/premium/ads/tracker")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["watches_today"]["revive"] == 1
        assert len(body["data"]["watch_history"]) == 1

    @pytest.mark.asyncio
    async def test_get_tracker_no_auth(self, unauth_client: AsyncClient) -> None:
        """Should return 401/403 without auth."""
        response = await unauth_client.get("/premium/ads/tracker")
        assert response.status_code in (401, 403)
