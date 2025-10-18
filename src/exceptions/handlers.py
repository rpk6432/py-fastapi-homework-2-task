from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from routes.movies import update_movie


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        if request.scope.get("endpoint") is update_movie:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input data."},
            )
        return await request_validation_exception_handler(request, exc)
