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


@pytest.fixture
def db_session():
    import gallery.config as config
    import gallery.db as db

    gallery_config = config.get_config()
    db.init(gallery_config)

    session = next(db.session())
    
    yield session
    
    session.close()


@pytest.fixture
def image_service(db_session):
    from gallery.service import ImageService

    return ImageService(session=db_session)


@pytest.fixture
def user_service(db_session):
    from gallery.service import UserService

    return UserService(session=db_session)


@pytest.fixture
def auth_service(user_service):
    import gallery.config as config
    from gallery.service import AuthService
    
    gallery_config = config.get_config()

    return AuthService(user_service=user_service, config=gallery_config)


@pytest.fixture
def image_dir(tmp_path):
    import gallery.config as config

    image_dir = tmp_path / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    gallery_config = config.get_config()
    gallery_config.image_directory = str(image_dir)
    
    return image_dir
