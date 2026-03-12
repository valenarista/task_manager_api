import pytest
from starlette.requests import Request

from app.db import session as db_session_module
from app.main import log_requests


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_root_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}


def test_error_contract_for_duplicate_email(client):
    payload = {"email": "contract@example.com", "password": "StrongPass1"}
    first = client.post("/api/v1/users", json=payload)
    assert first.status_code == 200, first.text

    second = client.post("/api/v1/users", json=payload)
    assert second.status_code == 409, second.text
    data = second.json()
    assert data["detail"] == "Email already registered"
    assert data["error"]["code"] == "email_already_registered"
    assert data["error"]["message"] == "Email already registered"


def test_error_contract_for_validation_error(client):
    response = client.post(
        "/api/v1/users",
        json={"email": "bad-email", "password": "123"},
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert data["detail"] == "Validation failed"
    assert data["error"]["code"] == "validation_error"
    assert data["error"]["message"] == "Validation failed"
    assert isinstance(data["error"]["details"], list)


@pytest.mark.asyncio
async def test_log_requests_middleware_reraises_exceptions():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/boom",
            "headers": [],
            "query_string": b"",
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
            "root_path": "",
        }
    )

    async def failing_call_next(_: Request):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await log_requests(request, failing_call_next)


def test_get_db_yields_session_and_closes_it(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake_session = FakeSession()
    monkeypatch.setattr(db_session_module, "SessionLocal", lambda: fake_session)

    generator = db_session_module.get_db()
    yielded = next(generator)
    assert yielded is fake_session
    assert fake_session.closed is False

    generator.close()
    assert fake_session.closed is True

