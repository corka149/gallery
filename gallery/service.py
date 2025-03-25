from datetime import datetime
import logging
import os
import shutil
from os import path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, UploadFile
from PIL import Image
from sqlmodel import Session, select

import gallery.db as db
import gallery.config as config


class ImageService:
    def __init__(self, session: Annotated[Session, Depends(db.session)]):
        self.session = session
        self.config = config.load()

    def get_image(self, image_id):
        statement = select(db.Image).where(db.Image.id == image_id)
        result = self.session.exec(statement)
        return result.one()

    def get_images(self):
        statement = select(db.Image)
        result = self.session.exec(statement)
        return result.all()

    def save(self, image: db.Image, image_file: UploadFile):
        thumbnail_img_path = ""
        img_path = ""
        
        if image_file.filename:
            uuid = uuid4()
            image_dir = path.join(self.config.image_directory, str(uuid))
            
            logging.info(f"Saving image to {image_dir}")
            
            os.makedirs(image_dir, exist_ok=True)
            # tempfile.SpooledTemporaryFile
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

        image.url = img_path
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
