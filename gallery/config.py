import os
from enum import Enum

from pydantic import BaseModel


class AuthConfig(BaseModel):
    secret_token: str
    salt: str


class ReleaseMode(str, Enum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"

    def is_dev(self) -> bool:
        return self == ReleaseMode.DEV

    def is_prod(self) -> bool:
        return self == ReleaseMode.PROD

    def is_test(self) -> bool:
        return self == ReleaseMode.TEST


class Config(BaseModel):
    database_url: str
    image_directory: str
    gallery_endpoint: str
    auth: AuthConfig
    mode: ReleaseMode


def get_config():
    return Config(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://myadmin:mypassword@localhost:5432/gallery",
        ),
        image_directory=os.getenv("IMAGE_DIRECTORY", "/var/gallery/images"),
        gallery_endpoint=os.getenv("GALLERY_ENDPOINT", "/gallery/images"),
        auth=AuthConfig(
            secret_token=os.getenv("AUTH_SECRET_TOKEN", "mysecret"),
            salt=os.getenv("AUTH_SALT", "mysalt"),
        ),
        mode=ReleaseMode(
            os.getenv("RELEASE_MODE", ReleaseMode.DEV.value)
        ),
    )
