import alembic
from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture
def db_setup():
    alembic.config.main(
        argv=[
            "upgrade",
            "head",
        ]
    )
    yield
    alembic.config.main(
        argv=[
            "downgrade",
            "base",
        ]
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
