import logging
import time

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
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
def root():
    return {"message": "API is running"}