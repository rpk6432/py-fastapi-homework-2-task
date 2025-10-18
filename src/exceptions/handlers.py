from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        endpoint = request.scope.get("endpoint")
        if (
                endpoint
                and endpoint.__name__ == "update_movie"
                and endpoint.__module__.endswith("routes.movies")
        ):
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid input data."},
            )
        return await request_validation_exception_handler(request, exc)
