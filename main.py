from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile, responses, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import gallery.config as config
import gallery.db as db
from gallery.service import ImageService

config = config.load()
db.init(config)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    config.gallery_endpoint,
    StaticFiles(directory=config.image_directory),
    name="images",
)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, service: Annotated[ImageService, Depends()]):
    images = service.get_images()

    for image in images:
        image.url = image.url.replace(config.image_directory, config.gallery_endpoint)
        image.thumbnail_url = image.thumbnail_url.replace(
            config.image_directory, config.gallery_endpoint
        )

    return templates.TemplateResponse(
        request=request, name="home.html.jinja", context={"images": images}
    )


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html.jinja", context={}
    )


@app.get("/images/add", response_class=HTMLResponse)
def add_image(request: Request):
    return templates.TemplateResponse(
        request=request, name="add_image.html.jinja", context={}
    )


@app.post("/images/add", response_class=HTMLResponse)
def create_image(
    image: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    tags: Annotated[str, Form()],
    service: Annotated[ImageService, Depends()],
):
    imageData = db.Image(
        title=title,
        description=description,
        tags=tags,
    )

    service.save(imageData, image)

    return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/images/{image_id}/delete", response_class=HTMLResponse)
def delete_image(request: Request, image_id: int, service: Annotated[ImageService, Depends()]):
    service.delete(image_id)
    return responses.RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
