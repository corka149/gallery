import logging
import os
import shutil
from datetime import datetime
from os import path
from typing import Annotated, Optional
from uuid import uuid4

from argon2 import PasswordHasher
from fastapi import Depends, UploadFile
from itsdangerous import URLSafeSerializer
from PIL import Image
from sqlmodel import Session, select

import gallery.config as config
import gallery.db as db


class ImageService:
    def __init__(self, session: Annotated[Session, Depends(db.session)]):
        self.session = session
        self.config = config.get_config()

    def get_image(self, image_id):
        statement = select(db.Image).where(db.Image.id == image_id)
        result = self.session.exec(statement)
        return result.one_or_none()

    def get_images(self):
        statement = select(db.Image)
        result = self.session.exec(statement)
        return result.all()

    def save(self, image: db.Image, image_file: Optional[UploadFile]):
        img_path = ""
        thumbnail_img_path = ""

        if image_file and image_file.filename != "":
            uuid = uuid4()
            image_dir = path.join(self.config.image_directory, str(uuid))

            logging.info(f"Saving image to {image_dir}")

            os.makedirs(image_dir, exist_ok=True)
            
            thumbnail_img_path = path.join(image_dir, "thumbnail.jpg")
            img_path = path.join(image_dir, image_file.filename)

            with open(img_path, mode="w+b") as i:
                i.write(image_file.file.read())

            with Image.open(img_path) as img:
                width, height = img.size
                new_size = (width // 10, height // 10)
                thumbnail_img = img.copy()
                thumbnail_img.thumbnail(new_size)
                thumbnail_img.save(thumbnail_img_path)

        if img_path:
            image.url = img_path
            
        if thumbnail_img_path:
            image.thumbnail_url = thumbnail_img_path
            
        image.created_at = image.created_at or datetime.now()
        image.updated_at = datetime.now()

        self.session.add(image)
        self.session.commit()

        return image

    def delete(self, image_id: int):
        statement = select(db.Image).where(db.Image.id == image_id)
        result = self.session.exec(statement)
        image = result.one()
        self.session.delete(image)
        self.session.commit()

        shutil.rmtree(path.dirname(image.url))

        return image


class UserService:
    def __init__(self, session: Annotated[Session, Depends(db.session)]):
        self.session = session
        self.ph = PasswordHasher()

    def get_user(self, username: str):
        statement = select(db.User).where(db.User.username == username)
        result = self.session.exec(statement)
        return result.one()

    def save(self, user: db.User, password: str = None):
        if password:
            user.password_hash = self.ph.hash(password)

        self.session.add(user)
        self.session.commit()
        return user

    def delete(self, user_id: int):
        statement = select(db.User).where(db.User.id == user_id)
        result = self.session.exec(statement)
        user = result.one()
        self.session.delete(user)
        self.session.commit()
        return user


class AuthService:
    def __init__(
        self,
        user_service: Annotated[UserService, Depends()],
        config: Annotated[config.Config, Depends(config.get_config)],
    ):
        self.serializer = URLSafeSerializer(
            config.auth.secret_token, salt=config.auth.salt
        )
        self.user_service = user_service
        self.ph = PasswordHasher()

    def verify(self, username: str, password: str) -> bool:
        user = self.user_service.get_user(username)

        if user is None:
            return False

        try:
            self.ph.verify(user.password_hash, password)

            if self.ph.check_needs_rehash(user.password_hash):
                user.password_hash = self.ph.hash(password)
                self.user_service.save(user)

            return True
        except Exception:
            return False

    def generate_token(self, username: str) -> str:
        return self.serializer.dumps(username)

    def verify_token(self, token: str) -> str:
        try:
            return self.serializer.loads(token)
        except Exception:
            return None
