import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.routes import users as users_route_module
from app.db import session as db_session_module
from app.main import app, log_requests
from tests.conftest import unique_email


def create_user_and_login(client):
    email = unique_email()
    password = "StrongPass1"

    create = client.post("/api/v1/users", json={"email": email, "password": password})
    assert create.status_code == 200, create.text

    login = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
    assert data["error"]["details"]
    assert {"loc", "msg", "type"}.issubset(data["error"]["details"][0].keys())


def test_error_contract_for_not_authenticated(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Not authenticated"
    assert data["error"]["code"] == "http_401"
    assert data["error"]["message"] == "Not authenticated"
    assert "details" not in data["error"]


def test_error_contract_for_login_invalid_credentials(client):
    email = unique_email()
    password = "StrongPass1"

    create = client.post("/api/v1/users", json={"email": email, "password": password})
    assert create.status_code == 200, create.text

    response = client.post(
        "/api/v1/login",
        data={"username": email, "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Invalid email or password"
    assert data["error"]["code"] == "invalid_credentials"
    assert data["error"]["message"] == "Invalid email or password"


def test_error_contract_for_task_not_found(client):
    auth_headers = create_user_and_login(client)

    response = client.patch(
        "/api/v1/tasks/9999",
        json={"done": True},
        headers=auth_headers,
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Task not found"
    assert data["error"]["code"] == "task_not_found"
    assert data["error"]["message"] == "Task not found"


def test_internal_server_error_does_not_leak_details(client, monkeypatch, caplog):
    def boom(_: str) -> str:
        raise RuntimeError("database exploded")

    monkeypatch.setattr(users_route_module, "hash_password", boom)

    with TestClient(app, raise_server_exceptions=False) as safe_client:
        response = safe_client.post(
            "/api/v1/users",
            json={"email": "boom@example.com", "password": "StrongPass1"},
        )
    assert response.status_code == 500, response.text
    data = response.json()
    assert data["detail"] == "Internal server error"
    assert data["error"]["code"] == "internal_error"
    assert data["error"]["message"] == "Internal server error"
    assert "details" not in data["error"]
    assert "database exploded" not in response.text
    assert "Unhandled exception while processing POST /api/v1/users" in caplog.text
    assert "database exploded" in caplog.text


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

