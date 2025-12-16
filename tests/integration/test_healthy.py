import pytest
from fastapi import status

from configs.settings import settings


class TestHealthyEndpoint:
    """Integration tests for the /healthy endpoint."""

    @pytest.mark.asyncio
    async def test_healthy_endpoint(self, async_client):
        res = await async_client.get(f"/api/{settings.APP_VERSION}/healthy")
        data = res.json()

        assert "status" in data
        assert "app" in data
        assert "version" in data
        assert res.status_code == status.HTTP_200_OK
