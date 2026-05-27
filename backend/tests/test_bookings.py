"""Tests for booking endpoints.

These tests require a running server at http://localhost:8000.
They are automatically skipped when the server is not available.
Run manually with: pytest backend/tests/test_bookings.py -v
"""
import socket
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timezone


def _server_available(host: str = "localhost", port: int = 8000) -> bool:
    """Return True if the dev/prod server is reachable."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


requires_server = pytest.mark.skipif(
    not _server_available(),
    reason="Live server not running at localhost:8000 — skipping live-integration tests",
)


@pytest.fixture
def base_url():
    return "http://localhost:8000"


@pytest.fixture
def admin_token():
    """Login as admin and return token."""
    return None


@requires_server
@pytest.mark.anyio
async def test_list_vendors(base_url):
    from httpx import AsyncClient
    async with AsyncClient() as client:
        response = await client.get(f"{base_url}/api/vendors", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@requires_server
@pytest.mark.anyio
async def test_vendor_admin_stats(base_url):
    """Get vendor reliability stats via admin API."""
    from httpx import AsyncClient
    import os

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@shadiro.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    async with AsyncClient() as client:
        login_response = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        vendors_response = await client.get(f"{base_url}/api/admin/vendors", headers=headers)
        assert vendors_response.status_code == 200
        vendors = vendors_response.json()

        if vendors:
            vendor_id = vendors[0]["id"]
            stats_response = await client.get(
                f"{base_url}/api/admin/vendors/{vendor_id}/stats",
                headers=headers
            )
            assert stats_response.status_code == 200
            stats = stats_response.json()
            assert "vendor_id" in stats
            assert "total_bookings" in stats


@requires_server
@pytest.mark.anyio
async def test_reliability_report(base_url):
    """Get vendor reliability report via admin API."""
    from httpx import AsyncClient
    import os

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@shadiro.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    async with AsyncClient() as client:
        login_response = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        report_response = await client.get(
            f"{base_url}/api/admin/vendors/reliability-report",
            headers=headers,
            params={"limit": 100}
        )
        assert report_response.status_code == 200
        report = report_response.json()
        assert "vendors" in report
        if report["vendors"]:
            vendor = report["vendors"][0]
            if "acceptance_rate" in vendor:
                assert isinstance(vendor["acceptance_rate"], (int, float))
            if "emergency_count" in vendor:
                assert isinstance(vendor["emergency_count"], int)
            if "completed_count" in vendor:
                assert isinstance(vendor["completed_count"], int)


@requires_server
@pytest.mark.anyio
async def test_booking_operations_flow(base_url):
    """Test booking creation and vendor actions (if user token available)."""
    from httpx import AsyncClient
    import uuid

    async with AsyncClient() as client:
        booking_payload = {
            "user_id": str(uuid.uuid4()),
            "vendor_id": None,
            "items": [{"name": "Test Item", "qty": 1, "unit_price": 1000}],
            "total_amount": 1000,
            "status": "pending"
        }
        response = await client.post(
            f"{base_url}/api/bookings",
            json=booking_payload
        )
        # Either 401 (unauthorized), 403 (forbidden), or 422 (unprocessable) is expected
        assert response.status_code in [401, 403, 422]


@requires_server
@pytest.mark.anyio
async def test_get_bookings_admin(base_url):
    """List bookings via admin API."""
    from httpx import AsyncClient
    import os

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@shadiro.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    async with AsyncClient() as client:
        login_response = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": admin_email, "password": admin_password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        bookings_response = await client.get(
            f"{base_url}/api/bookings",
            headers=headers
        )
        assert bookings_response.status_code == 200
        bookings = bookings_response.json()
        assert isinstance(bookings, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
