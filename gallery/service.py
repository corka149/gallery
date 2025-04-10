import logging
import os
import shutil
from datetime import datetime, timedelta
from os import path
from typing import Annotated, List, Optional
from uuid import uuid4

from argon2 import PasswordHasher
from fastapi import Depends, UploadFile
from itsdangerous import URLSafeSerializer
from PIL import Image
from sqlmodel import Session, select

from gallery import dto
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

    def get_image_page(self, page_no: int, page_size: int, category: str):
        statement = (
            select(db.Image).where(db.Image.category == category)
            if category
            else select(db.Image)
        )

        result = self.session.exec(statement)
        images = result.all()

        total = len(images)
        total_pages = (total + page_size - 1) // page_size
        has_next = page_no < total_pages
        has_previous = page_no > 1

        start_index = (page_no - 1) * page_size
        end_index = start_index + page_size
        images = images[start_index:end_index]

        content: List[dto.ImageDTO] = []

        for image in images:
            image.url = image.url.replace(
                self.config.image_directory, self.config.gallery_endpoint
            )
            image.thumbnail_url = image.thumbnail_url.replace(
                self.config.image_directory, self.config.gallery_endpoint
            )

            content.append(
                dto.ImageDTO(
                    title=image.title,
                    description=image.description,
                    category=image.category,
                    image_url=image.url,
                    thumbnail_url=image.thumbnail_url,
                )
            )

        return {
            "page_no": page_no,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "content": content,
        }


class UserService:
    def __init__(self, session: Annotated[Session, Depends(db.session)]):
        self.session = session
        self.ph = PasswordHasher()

    def get_user(self, username: str):
        statement = select(db.User).where(db.User.username == username)
        result = self.session.exec(statement)
        return result.one_or_none()

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
        now = datetime.now()
        now += timedelta(hours=2)
        data = (username, now.timestamp())
        return self.serializer.dumps(data)

    def verify_token(self, token: str) -> str:
        try:
            (username, created_at) = self.serializer.loads(token)
            if created_at < datetime.now().timestamp():
                return None

            return username
        except Exception:
            return None
