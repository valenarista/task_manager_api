from typing import Any


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
