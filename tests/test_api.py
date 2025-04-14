import pathlib
from fastapi.testclient import TestClient

from gallery import api, db
from gallery.service import ImageService, UserService


def test_home_without_auth(client: TestClient):
    response = client.get("/")
    assert response.is_success
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Gallery" in response.text
    assert "Anmelden" in response.text


def test_home_with_auth(
    client: TestClient,
    user_service: UserService,
    image_service: ImageService,
    image_dir: pathlib.Path,
):
    _login(client, user_service)

    image = db.Image(
        title="some_image_with_auth",
        description="some_description",
        category="some_category",
        url=str(image_dir / "some_image.jpg"),
        thumbnail_url=str(image_dir / "some_thumbnail_image.jpg"),
    )
    image = image_service.save(image, None)

    response = client.get("/")
    assert response.is_success
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Gallery" in response.text
    assert "some_image_with_auth" in response.text
    assert "some_category" in response.text


def test_login_and_logout(client: TestClient, user_service: UserService):
    _login(client, user_service)

    # Test logout
    response = client.get("/logout")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Anmelden" in response.text


def test_failed_login(client: TestClient, user_service: UserService):
    # Create a user and save it to the database
    user = db.User(username="some_user", email="some_user@example.xyz")
    password = "some_password"
    user_service.save(user, password)

    # Test login
    response = client.post(
        "/login", data={"username": user.username, "password": password + "wrong"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Ungültiger Benutzername oder Passwort" in response.text


def test_hit_rate_limit(client: TestClient, user_service: UserService):
    # Create a user and save it to the database
    user = db.User(username="some_user", email="some_user@example.xyz")
    password = "some_password"
    user_service.save(user, password)

    # Test login
    for _ in range(6):
        response = client.post(
            "/login", data={"username": user.username, "password": password + "wrong"}
        )

    assert response.status_code == 429


def test_delete_image(
    client: TestClient,
    image_service: ImageService,
    user_service: UserService,
    image_dir: pathlib.Path,
):
    _login(client, user_service)

    # Create an image and save it to the database
    image = db.Image(
        title="some_image",
        description="some_description",
        category="some_category",
        url=str(image_dir / "some_image.jpg"),
        thumbnail_url=str(image_dir / "some_thumbnail_image.jpg"),
    )
    image = image_service.save(image, None)

    # Test delete image
    response = client.get(f"/images/{image.id}/delete")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"

    image = image_service.get_image(image.id)
    assert image is None


def test_login_form(client: TestClient):
    response = client.get("/login")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Anmelden" in response.text
    assert "Benutzername" in response.text
    assert "Passwort" in response.text


def test_add_image_form(client: TestClient, user_service: UserService):
    _login(client, user_service)

    response = client.get("/images/add")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Füge neues Bild hinzu" in response.text
    assert "Titel" in response.text
    assert "Beschreibung" in response.text
    assert "Kategorie" in response.text
    assert "Bild" in response.text


def test_cannot_add_image_without_auth(client: TestClient):
    response = client.get("/images/add")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Anmelden" in response.text
    assert "Füge neues Bild hinzu" not in response.text


def test_edit_image_form(
    client: TestClient,
    user_service: UserService,
    image_service: ImageService,
    image_dir: pathlib.Path,
):
    _login(client, user_service)

    # Create an image and save it to the database
    image = db.Image(
        title="some_image_edit",
        description="some_description",
        category=db.Category.ANNIVERSARY,
        url=str(image_dir / "some_image.jpg"),
        thumbnail_url=str(image_dir / "some_thumbnail_image.jpg"),
    )
    image = image_service.save(image, None)

    response = client.get(f"/images/{image.id}/edit")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Bild speichern" in response.text
    assert "Titel" in response.text
    assert "some_image_edit" in response.text
    assert "Beschreibung" in response.text
    assert "some_description" in response.text
    assert "Kategorie" in response.text

    any_selected = False
    for line in response.text.splitlines():
        if db.Category.ANNIVERSARY in line:
            any_selected = "selected" in line

    assert any_selected, "Category Anniversary should be selected"


def test_cannot_edit_without_auth(
    client: TestClient,
    user_service: UserService,
    image_service: ImageService,
    image_dir: pathlib.Path,
):
    # Create an image and save it to the database
    image = db.Image(
        title="some_image_edit",
        description="some_description",
        category=db.Category.ANNIVERSARY,
        url=str(image_dir / "some_image.jpg"),
        thumbnail_url=str(image_dir / "some_thumbnail_image.jpg"),
    )
    image = image_service.save(image, None)

    response = client.get(f"/images/{image.id}/edit")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Anmelden" in response.text
    assert "Bild speichern" not in response.text


def test_get_gallery(
    client: TestClient,
    user_service: UserService,
    image_service: ImageService,
    image_dir: pathlib.Path,
):
    _login(client, user_service)

    # Create images and save it to the database
    for i in range(api.PAGE_SIZE + 1):
        image = db.Image(
            title=f"some_image_{i}",
            description="some_description",
            category=db.Category.ANNIVERSARY,
            url=str(image_dir / "some_image.jpg"),
            thumbnail_url=str(image_dir / "some_thumbnail_image.jpg"),
        )
        image = image_service.save(image, None)

    response = client.get("/images/gallery")
    assert response.status_code == 200
    assert response.json()["page_no"] == 1
    assert response.json()["page_size"] == api.PAGE_SIZE
    assert response.json()["total"] == api.PAGE_SIZE + 1
    assert response.json()["total_pages"] == 2
    assert response.json()["has_next"] is True
    assert response.json()["has_previous"] is False
    assert len(response.json()["content"]) == api.PAGE_SIZE
    
    # Next page
    response = client.get("/images/gallery?page=2")
    assert response.status_code == 200
    assert response.json()["page_no"] == 2
    assert response.json()["page_size"] == api.PAGE_SIZE
    assert response.json()["total"] == api.PAGE_SIZE + 1
    assert response.json()["total_pages"] == 2
    assert response.json()["has_next"] is False
    assert response.json()["has_previous"] is True
    assert len(response.json()["content"]) == 1


def _login(client: TestClient, user_service: UserService):
    # Create a user and save it to the database
    user = db.User(username="some_user", email="some_user@example.xyz")
    password = "some_password"
    user_service.save(user, password)

    # Test login
    response = client.post(
        "/login", data={"username": user.username, "password": password}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Abmelden" in response.text
