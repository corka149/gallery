
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import alembic.config
import gallery.config as config
import gallery.db as db
import gallery.api as api

gallery_config = config.get_config()
db.init(gallery_config)

# Run migrations
alembic.config.main(
    argv=[
        "upgrade",
        "head",
    ]
)

# Initialize app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    gallery_config.gallery_endpoint,
    StaticFiles(directory=gallery_config.image_directory),
    name="images",
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


api.configure(app, limiter, gallery_config)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
