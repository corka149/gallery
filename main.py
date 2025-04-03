import gettext
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile, responses, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import alembic.config
import gallery.config as config
import gallery.db as db
from gallery.service import ImageService, AuthService as Auth

config = config.get_config()
db.init(config)

# Run migrations
alembic.config.main(
    argv=[
        "upgrade",
        "head",
    ]
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    config.gallery_endpoint,
    StaticFiles(directory=config.image_directory),
    name="images",
)

# Set up translations
language_translations = gettext.translation("base", "locales", languages=["de", "en"])
language_translations.install()
_ = language_translations.gettext

templates = Jinja2Templates(directory="templates")


class TemplateRenderer:
    def __init__(self, request: Request, auth: Annotated[Auth, Depends()]):
        self.auth = auth
        self.request = request

    def render(self, name: str, context: dict):
        context["_"] = _
        context["is_authenticated"] = False
        if self.request.cookies.get("gallery"):
            token = self.request.cookies.get("gallery")
            username = self.auth.verify_token(token)
            if username:
                context["is_authenticated"] = True

        return templates.TemplateResponse(
            request=self.request, name=name, context=context
        )


def is_authenticated(request: Request, auth: Annotated[Auth, Depends()]):
    token = request.cookies.get("gallery")

    if token:
        return auth.verify_token(token)
    return False


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
def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth: Annotated[Auth, Depends()],
    renderer: Annotated[TemplateRenderer, Depends()],
):
    if not auth.verify(username, password):
        return renderer.render(
            name="login.html.jinja",
            context={"errors": [_("Invalid username or password")]},
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
    
    return renderer.render(name="add_image.html.jinja", context={})


@app.post("/images/add", response_class=HTMLResponse)
def create_image(
    image: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    service: Annotated[ImageService, Depends()],
    is_authenticated: Annotated[bool, Depends(is_authenticated)],
):
    if not is_authenticated:
        return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    imageData = db.Image(
        title=title,
        description=description,
        tags=tags,
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

    return renderer.render(name="edit_image.html.jinja", context={"image": image})


@app.post("/images/{image_id}/edit", response_class=HTMLResponse)
def update_image(
    image_id: int,
    image: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    service: Annotated[ImageService, Depends()],
    is_authenticated: Annotated[bool, Depends(is_authenticated)],
):
    if not is_authenticated:
        return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    imageData = service.get_image(image_id)

    imageData.title = title
    imageData.description = description
    imageData.tags = tags

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
