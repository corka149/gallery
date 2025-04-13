
from fastapi.testclient import TestClient


def test_home_without_auth(db_setup, client: TestClient):
    response = client.get("/")
    assert response.is_success
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Gallery" in response.text
