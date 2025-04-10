from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile, responses, status
from fastapi.responses import HTMLResponse
from slowapi import Limiter


from gallery.config import Config
import gallery.db as db
from gallery.service import ImageService, AuthService as Auth
from gallery.templates import TemplateRenderer


def is_authenticated(request: Request, auth: Annotated[Auth, Depends()]):
    token = request.cookies.get("gallery")

    if token:
        return auth.verify_token(token)
    return False


def configure(app: FastAPI, limiter: Limiter, config: Config):
    
    @app.get("/", response_class=HTMLResponse)
    def home(
        service: Annotated[ImageService, Depends()],
        renderer: Annotated[TemplateRenderer, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        images = []

        if is_authenticated:
            images = service.get_images()

        for image in images:
            image.url = image.url.replace(config.image_directory, config.gallery_endpoint)
            image.thumbnail_url = image.thumbnail_url.replace(
                config.image_directory, config.gallery_endpoint
            )

        return renderer.render(name="home.html.jinja", context={"images": images})


    @app.get("/login", response_class=HTMLResponse)
    def login_form(renderer: Annotated[TemplateRenderer, Depends()]):
        return renderer.render(name="login.html.jinja", context={})


    @app.post("/login", response_class=HTMLResponse)
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

        response = responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

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


    @app.get("/logout", response_class=HTMLResponse)
    def logout():
        response = responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key="gallery")
        return response


    @app.get("/images/add", response_class=HTMLResponse)
    def add_image(
        renderer: Annotated[TemplateRenderer, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        return renderer.render(name="add_image.html.jinja", context={"categories": db.Category})


    @app.post("/images/add", response_class=HTMLResponse)
    def create_image(
        image: Annotated[UploadFile, File()],
        title: Annotated[str, Form()],
        description: Annotated[str, Form()],
        category: Annotated[str, Form()],
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        imageData = db.Image(
            title=title,
            description=description,
            category=category,
        )

        service.save(imageData, image)

        return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


    @app.get("/images/{image_id}/edit", response_class=HTMLResponse)
    def edit_image(
        image_id: int,
        renderer: Annotated[TemplateRenderer, Depends()],
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        image = service.get_image(image_id)
        image.url = image.url.replace(config.image_directory, config.gallery_endpoint)
        image.thumbnail_url = image.thumbnail_url.replace(
            config.image_directory, config.gallery_endpoint
        )

        return renderer.render(name="edit_image.html.jinja", context={"image": image, "categories": db.Category})


    @app.post("/images/{image_id}/edit", response_class=HTMLResponse)
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
            return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        imageData = service.get_image(image_id)

        imageData.title = title
        imageData.description = description
        imageData.category = category

        service.save(imageData, image)

        return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


    @app.get("/images/{image_id}/delete", response_class=HTMLResponse)
    def delete_image(
        image_id: int,
        service: Annotated[ImageService, Depends()],
        is_authenticated: Annotated[bool, Depends(is_authenticated)],
    ):
        if not is_authenticated:
            return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        service.delete(image_id)
        return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
