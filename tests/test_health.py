"""
Smoke tests — verify the application starts and exposes the expected routes.
These run fast (no real network I/O) and serve as a CI baseline.
"""

import pytest
from httpx import AsyncClient


def test_app_instance():
    from app.main import app

    assert app.title == "Network Monitoring Utility"


def test_settings_defaults():
    from app.config import settings

    assert settings.app_name
    assert "sqlite" in settings.database_url
    assert settings.monitoring_interval_seconds > 0


def test_routes_registered():
    from app.main import app

    paths = {r.path for r in app.routes}
    assert "/nodes" in paths
    assert "/logs" in paths


@pytest.mark.asyncio
async def test_openapi_reachable(client: AsyncClient):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "Network Monitoring" in data["info"]["title"]


@pytest.mark.asyncio
async def test_nodes_list_empty(client: AsyncClient):
    """Fresh DB should return an empty list, not an error."""
    response = await client.get("/nodes")
    assert response.status_code == 200
    assert response.json() == []
