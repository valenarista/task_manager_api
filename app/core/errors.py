from typing import Any

from fastapi import HTTPException

INVALID_CREDENTIALS_CODE = "invalid_credentials"
INVALID_CREDENTIALS_MESSAGE = "Could not validate credentials"
LOGIN_INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
TASK_NOT_FOUND_CODE = "task_not_found"
TASK_NOT_FOUND_MESSAGE = "Task not found"
EMAIL_ALREADY_REGISTERED_CODE = "email_already_registered"
EMAIL_ALREADY_REGISTERED_MESSAGE = "Email already registered"


def api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> HTTPException:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def invalid_credentials_error() -> HTTPException:
    return api_error(
        status_code=401,
        code=INVALID_CREDENTIALS_CODE,
        message=INVALID_CREDENTIALS_MESSAGE,
    )


def login_invalid_credentials_error() -> HTTPException:
    return api_error(
        status_code=400,
        code=INVALID_CREDENTIALS_CODE,
        message=LOGIN_INVALID_CREDENTIALS_MESSAGE,
    )


def task_not_found_error() -> HTTPException:
    return api_error(
        status_code=404,
        code=TASK_NOT_FOUND_CODE,
        message=TASK_NOT_FOUND_MESSAGE,
    )


def email_already_registered_error() -> HTTPException:
    return api_error(
        status_code=409,
        code=EMAIL_ALREADY_REGISTERED_CODE,
        message=EMAIL_ALREADY_REGISTERED_MESSAGE,
    )


def build_error_payload(
    *,
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details is not None:
        error["details"] = details

    return {
        "error": error,
        "detail": message,
    }


def resolve_http_error(detail: Any, status_code: int) -> tuple[str, str, Any | None]:
    code = f"http_{status_code}"

    if isinstance(detail, str):
        return code, detail, None

    if isinstance(detail, dict):
        resolved_code = str(detail.get("code", code))
        message = str(detail.get("message", detail.get("detail", "Request failed")))
        details = detail.get("details")
        return resolved_code, message, details

    if isinstance(detail, list):
        return code, "Request failed", detail

    return code, "Request failed", None
