import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import build_error_payload, resolve_http_error
from app.core.logging_config import clear_request_id, get_request_id, set_request_id, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_ID_HEADER = "X-Request-ID"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code, message, details = resolve_http_error(exc.detail, exc.status_code)
    logger.warning(
        "http_error method=%s path=%s status_code=%s code=%s message=%s",
        request.method,
        request.url.path,
        exc.status_code,
        code,
        message,
    )
    payload = build_error_payload(code=code, message=message, details=details)
    request_id = getattr(request.state, "request_id", get_request_id())
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "validation_error method=%s path=%s status_code=422 errors=%s",
        request.method,
        request.url.path,
        len(exc.errors()),
    )
    payload = build_error_payload(
        code="validation_error",
        message="Validation failed",
        details=exc.errors(),
    )
    request_id = getattr(request.state, "request_id", get_request_id())
    return JSONResponse(
        status_code=422,
        content=payload,
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    payload = build_error_payload(
        code="internal_error",
        message="Internal server error",
    )
    request_id = getattr(request.state, "request_id", get_request_id())
    return JSONResponse(
        status_code=500,
        content=payload,
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER, "").strip() or uuid.uuid4().hex
    request.state.request_id = request_id
    set_request_id(request_id)
    start_time = time.perf_counter()
    logger.info("request_started method=%s path=%s", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "request_failed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            500,
            duration_ms,
        )
        clear_request_id()
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id

    logger.info(
        "request_finished method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    clear_request_id()

    return response


app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "API is running"}
