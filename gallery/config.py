import os

from pydantic import BaseModel


class Config(BaseModel):
    database_url: str


def load():
    return Config(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql+psycopg://myadmin:mypassword@localhost:5432/gallery"
        )
    )
