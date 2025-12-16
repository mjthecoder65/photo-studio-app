import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app

BASE_URL = "http://test"


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for the FastAPI application."""

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        yield client
