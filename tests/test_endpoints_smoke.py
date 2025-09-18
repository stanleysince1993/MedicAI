import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
