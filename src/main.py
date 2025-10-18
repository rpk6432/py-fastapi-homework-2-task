from fastapi import FastAPI

from exceptions import register_exception_handlers
from routes import movie_router


app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

register_exception_handlers(app)

api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
