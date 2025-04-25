import logging
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile, responses, status
from fastapi.responses import HTMLResponse
from slowapi import Limiter

import gallery.db as db
from gallery import dto
from gallery.config import Config
from gallery.service import AuthService as Auth
from gallery.service import ImageService
from gallery.templates import TemplateRenderer

PAGE_SIZE = 10


def is_authenticated(request: Request, auth: Annotated[Auth, Depends()]):
    token = request.cookies.get("gallery")

    if token:
        return auth.verify_token(token)
    return False


def configure(app: FastAPI, limiter: Limiter, config: Config):
    @app.get("/a/", response_class=HTMLResponse)
    def home(
        service: Annotated[ImageService, Depends()],
        renderer: Annotated[TemplateRenderer, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        images = []

        if is_authenticated:
            images = service.get_images()

        for image in images:
            image.url = image.url.replace(
                config.image_directory, config.gallery_endpoint
            )
            image.thumbnail_url = image.thumbnail_url.replace(
                config.image_directory, config.gallery_endpoint
            )

        return renderer.render(name="home.html.jinja", context={"images": images})

    @app.get("/a/login", response_class=HTMLResponse)
    def login_form(renderer: Annotated[TemplateRenderer, Depends()]):
        return renderer.render(name="login.html.jinja", context={})

    @app.post("/a/login", response_class=HTMLResponse)
    @limiter.limit("5/minute")
    def login(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        auth: Annotated[Auth, Depends()],
        renderer: Annotated[TemplateRenderer, Depends()],
    ):
        if not auth.verify(username, password):
            error = renderer.translate("Invalid username or password")

            return renderer.render(
                name="login.html.jinja",
                context={"errors": [error]},
            )

        response = responses.RedirectResponse(
            url="/a/", status_code=status.HTTP_302_FOUND
        )

        token = auth.generate_token(username)

        response.set_cookie(
            key="gallery",
            value=token,
            max_age=3200,  # 60 minutes
            httponly=True,
            secure=config.mode.is_prod(),  # Only set secure cookies in production (Uses HTTPS)
            samesite="Strict",
        )

        return response

    @app.get("/a/logout", response_class=HTMLResponse)
    def logout():
        response = responses.RedirectResponse(
            url="/a/", status_code=status.HTTP_302_FOUND
        )
        response.delete_cookie(key="gallery")
        return response

    @app.get("/a/images/add", response_class=HTMLResponse)
    def add_image(
        renderer: Annotated[TemplateRenderer, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(
                url="/a/", status_code=status.HTTP_302_FOUND
            )

        return renderer.render(
            name="add_image.html.jinja", context={"categories": db.Category}
        )

    @app.post("/a/images/add", response_class=HTMLResponse)
    def create_image(
        image: Annotated[UploadFile, File()],
        title: Annotated[str, Form()],
        description: Annotated[str, Form()],
        category: Annotated[str, Form()],
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(
                url="/a/", status_code=status.HTTP_302_FOUND
            )

        imageData = db.Image(
            title=title,
            description=description,
            category=category,
        )

        service.save(imageData, image)

        return responses.RedirectResponse(url="/a/", status_code=status.HTTP_302_FOUND)

    @app.get("/a/images/{image_id}/edit", response_class=HTMLResponse)
    def edit_image(
        image_id: int,
        renderer: Annotated[TemplateRenderer, Depends()],
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(
                url="/a/", status_code=status.HTTP_302_FOUND
            )

        image = service.get_image(image_id)
        image.url = image.url.replace(config.image_directory, config.gallery_endpoint)
        image.thumbnail_url = image.thumbnail_url.replace(
            config.image_directory, config.gallery_endpoint
        )

        return renderer.render(
            name="edit_image.html.jinja",
            context={"image": image, "categories": db.Category},
        )

    @app.post("/a/images/{image_id}/edit", response_class=HTMLResponse)
    def update_image(
        image_id: int,
        image: Annotated[UploadFile, File()],
        title: Annotated[str, Form()],
        description: Annotated[str, Form()],
        category: Annotated[str, Form()],
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(
                url="/a/", status_code=status.HTTP_302_FOUND
            )

        imageData = service.get_image(image_id)

        imageData.title = title
        imageData.description = description
        imageData.category = category

        service.save(imageData, image)

        return responses.RedirectResponse(url="/a/", status_code=status.HTTP_302_FOUND)

    @app.get("/a/images/{image_id}/delete", response_class=HTMLResponse)
    def delete_image(
        image_id: int,
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(
                url="/a/", status_code=status.HTTP_302_FOUND
            )

        service.delete(image_id)
        return responses.RedirectResponse(url="/a/", status_code=status.HTTP_302_FOUND)

    @app.get("/a/images/gallery")
    @limiter.limit("30/minute")
    def get_gallery(
        request: Request,
        service: Annotated[ImageService, Depends()],
        page: int = 1,
        category: str = "",
    ) -> dto.Page:
        try:
            return service.get_image_page(page, PAGE_SIZE, category)
        except Exception as e:
            logging.error(f"Error fetching images: {e}")

            return dto.Page(
                page_no=1,
                page_size=0,
                total=0,
                total_pages=0,
                has_next=False,
                has_previous=False,
                content=[],
            )

    @app.get("/a/images/categories")
    @limiter.limit("30/minute")
    def get_categories(
        request: Request,
        service: Annotated[ImageService, Depends()],
        renderer: Annotated[TemplateRenderer, Depends()],
    ) -> list[dto.CategoryDTO]:
        try:
            return [
                dto.CategoryDTO(
                    key=category,
                    name=renderer.translate(category),
                )
                for category in service.get_categories()
            ]
        except Exception as e:
            logging.error(f"Error fetching categories: {e}")
            return []
