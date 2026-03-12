import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.errors import build_error_payload, resolve_http_error
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code, message, details = resolve_http_error(exc.detail, exc.status_code)
    payload = build_error_payload(code=code, message=message, details=details)
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    payload = build_error_payload(
        code="validation_error",
        message="Validation failed",
        details=exc.errors(),
    )
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    payload = build_error_payload(
        code="internal_error",
        message="Internal server error",
    )
    return JSONResponse(status_code=500, content=payload)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception: 
        duration = time.time() - start_time
        logger.exception(
            "Request: %s %s -> 500 (%.4fs)",
            request.method,
            request.url.path,
            duration,
        )
        raise

    duration = time.time() - start_time

    logger.info(
        "Request: %s %s -> %s (%.4fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "API is running"}
