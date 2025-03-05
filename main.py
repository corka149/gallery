import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html.jinja", context={}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html.jinja", context={}
    )


@app.get("/images/add", response_class=HTMLResponse)
async def add_image(request: Request):
    return templates.TemplateResponse(
        request=request, name="add_image.html.jinja", context={}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
