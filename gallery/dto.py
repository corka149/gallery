from typing import List

from pydantic import BaseModel


class ImageDTO(BaseModel):
    title: str
    description: str
    category: str
    image_url: str
    thumbnail_url: str


class Page(BaseModel):
    page_no: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    content: List[ImageDTO]


class CategoryDTO(BaseModel):
    key: str
    name: str
