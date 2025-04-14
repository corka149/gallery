
from fastapi.testclient import TestClient

from gallery import db
from gallery.service import ImageService, UserService


def test_home_without_auth(db_setup, client: TestClient, image_service: ImageService):
    response = client.get("/")
    assert response.is_success
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Gallery" in response.text
    assert "Anmelden" in response.text


def test_login(db_setup, client: TestClient, user_service: UserService):
    user = db.User(username="some_user", email="some_user@example.xyz")
    password = "some_password"
    user_service.save(user, password)
    
    response = client.post("/login", data={"username": user.username, "password": password})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Abmelden" in response.text