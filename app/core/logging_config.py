import contextvars
import logging

REQUEST_ID_CONTEXT: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CONTEXT.get()
        return True


def set_request_id(request_id: str) -> None:
    REQUEST_ID_CONTEXT.set(request_id)


def get_request_id() -> str:
    return REQUEST_ID_CONTEXT.get()


def clear_request_id() -> None:
    REQUEST_ID_CONTEXT.set("-")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
    )
    request_id_filter = RequestIdFilter()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(request_id_filter)
