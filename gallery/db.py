from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine

import gallery.config as config

engine = None


def init(config: config.Config) -> None:
    global engine
    engine = create_engine(config.database_url, echo=True)


def session():
    s = Session(engine)
    
    try:
        yield s
    finally:
        s.close()


class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    tags: str
    url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, email={self.email})"
