import os

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient


@pytest.fixture(scope="session")
def app() -> FastAPI:
    os.environ["TESTING"] = "1"

    from api.server import get_application
    return get_application()


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    os.environ["TESTING"] = "1"
    async with LifespanManager(app):
        os.environ["TESTING"] = "1"
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"}
        ) as client:
            yield client
