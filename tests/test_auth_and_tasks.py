import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.routes.users import create_user as create_user_route
from app.core.security import create_access_token
from app.schemas.user import UserCreate
from tests.conftest import unique_email


def test_register_login_and_create_task(client):
    email = unique_email()
    password = "StrongPass1"

    r = client.post("/api/v1/users", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == email

    r = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token

    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/tasks",
        json={"title": "Mi primera task", "description": "testing"},
        headers=auth_headers,
    )
    assert r.status_code in (200, 201), r.text
    task = r.json()
    assert task["title"] == "Mi primera task"

    r = client.get("/api/v1/tasks", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    tasks = data["items"]
    assert isinstance(tasks, list)
    assert data["total"] >= 1
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert any(t["title"] == "Mi primera task" for t in tasks)


def test_login_wrong_password_fails(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    r = client.post(
        "/api/v1/login",
        data={"username": email, "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code in (400, 401), r.text

def create_user_and_login(client,email:str,password:str) -> str:
    r = client.post("/api/v1/users", json={"email": email, "password": password})
    assert r.status_code == 200, r.text

    r = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token
    return token

def test_user_cannot_access_anothers_users_task(client):
    password = "StrongPass1"
    email1 = unique_email()
    email2 = unique_email()

    token1 = create_user_and_login(client,email1,password)
    token2 = create_user_and_login(client,email2,password)

    auth_headers1 = {"Authorization": f"Bearer {token1}"}
    auth_headers2 = {"Authorization": f"Bearer {token2}"}

    r = client.post(
        "/api/v1/tasks",
        json={"title": "User1 Task", "description": "testing"},
        headers=auth_headers1,
    )
    assert r.status_code in (200, 201), r.text
    task1_id = r.json()["id"]

    r = client.get("/api/v1/tasks", headers=auth_headers2)
    assert r.status_code == 200, r.text
    data_2 = r.json()
    tasks_2 = data_2["items"]
    assert all(task["id"] != task1_id for task in tasks_2)

    r = client.patch(
        f"/api/v1/tasks/{task1_id}",
        json={"done": True},
        headers=auth_headers2,
    )
    assert r.status_code == 404, r.text

    r = client.delete(
        f"/api/v1/tasks/{task1_id}",
        headers=auth_headers2,
    )
    assert r.status_code == 404, r.text

def test_duplicate_email_registration_fails(client):
    email = unique_email()
    password = "StrongPass1"

    r = client.post("/api/v1/users", json={"email": email, "password": password})
    assert r.status_code == 200, r.text

    r = client.post("/api/v1/users", json={"email": email, "password": password})
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "Email already registered"

def test_access_protected_route_without_token_fails(client):
    r = client.get("/api/v1/tasks")
    assert r.status_code == 401, r.text

def test_me_without_token_fails(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 401, r.text

def test_me_with_token_returns_user_info(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)

    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/me", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == email

def test_update_nonexistent_task_returns_404(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.patch(
        "/api/v1/tasks/9999",
        json={"done": True},
        headers=auth_headers,
    )
    assert r.status_code == 404, r.text

def test_delete_nonexistent_task_returns_404(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.delete(
        "/api/v1/tasks/9999",
        headers=auth_headers,
    )
    assert r.status_code == 404, r.text

def test_list_tasks_with_done_filter(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/tasks",
        json={"title": "Task pendiente", "description": "A"},
        headers=auth_headers,
    )
    assert r.status_code in (200, 201), r.text
    task_1 = r.json()

    r = client.post(
        "/api/v1/tasks",
        json={"title": "Task completada", "description": "B"},
        headers=auth_headers,
    )
    assert r.status_code in (200, 201), r.text
    task_2 = r.json()

    r = client.patch(
        f"/api/v1/tasks/{task_2['id']}",
        json={"done": True},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = client.get("/api/v1/tasks?done=true", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    tasks = data["items"]
    assert data["total"] >= 1
    assert all(task["done"] is True for task in tasks)
    assert any(task["id"] == task_2["id"] for task in tasks)

    r = client.get("/api/v1/tasks?done=false", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    tasks = data["items"]
    assert data["total"] >= 1
    assert all(task["done"] is False for task in tasks)
    assert any(task["id"] == task_1["id"] for task in tasks)

def test_list_tasks_with_pagination(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        r = client.post(
            "/api/v1/tasks",
            json={"title": f"Task {i}", "description": f"Desc {i}"},
            headers=auth_headers,
        )
        assert r.status_code in (200, 201), r.text

    r = client.get("/api/v1/tasks?skip=0&limit=2", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    tasks = data["items"]
    assert len(tasks) == 2
    assert data["total"] >= 3
    assert data["skip"] == 0
    assert data["limit"] == 2

def test_list_limits_max_100(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/tasks?limit=150", headers=auth_headers)
    assert r.status_code == 422, r.text

def test_list_limits_min_1(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/tasks?limit=0", headers=auth_headers)
    assert r.status_code == 422, r.text

def test_list_skip_min_0(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/tasks?skip=-1", headers=auth_headers)
    assert r.status_code == 422, r.text


def test_update_task_title_and_description(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Old title", "description": "Old description"},
        headers=auth_headers,
    )
    assert create_response.status_code in (200, 201), create_response.text
    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "New title", "description": "New description"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200, update_response.text
    data = update_response.json()
    assert data["title"] == "New title"
    assert data["description"] == "New description"


def test_delete_existing_task_succeeds(client):
    email = unique_email()
    password = "StrongPass1"

    token = create_user_and_login(client, email, password)
    auth_headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/tasks",
        json={"title": "Task to delete", "description": "Delete me"},
        headers=auth_headers,
    )
    assert create_response.status_code in (200, 201), create_response.text
    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert delete_response.status_code == 204, delete_response.text

    list_response = client.get("/api/v1/tasks", headers=auth_headers)
    assert list_response.status_code == 200, list_response.text
    tasks = list_response.json()["items"]
    assert all(task["id"] != task_id for task in tasks)


def test_me_with_invalid_token_fails(client):
    auth_headers = {"Authorization": "Bearer invalid.token.value"}
    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 401, response.text


def test_me_with_token_without_sub_fails(client):
    token = create_access_token(data={"foo": "bar"})
    auth_headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 401, response.text


def test_me_with_token_for_nonexistent_user_fails(client):
    token = create_access_token(data={"sub": "ghost@example.com"})
    auth_headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 401, response.text


def test_create_user_handles_integrity_error_with_409():
    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class FakeDb:
        def __init__(self):
            self.rollback_called = False

        def query(self, *args, **kwargs):
            return FakeQuery()

        def add(self, obj):
            return None

        def commit(self):
            raise IntegrityError("insert into users", {"email": "x"}, Exception("dup"))

        def rollback(self):
            self.rollback_called = True

        def refresh(self, obj):
            return None

    db = FakeDb()
    user = UserCreate(email=unique_email(), password="StrongPass1")

    with pytest.raises(HTTPException) as exc_info:
        create_user_route(user=user, db=db)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "email_already_registered"
    assert exc_info.value.detail["message"] == "Email already registered"
    assert db.rollback_called is True


def test_create_user_reraises_unexpected_exception():
    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class FakeDb:
        def __init__(self):
            self.rollback_called = False

        def query(self, *args, **kwargs):
            return FakeQuery()

        def add(self, obj):
            return None

        def commit(self):
            raise RuntimeError("db unavailable")

        def rollback(self):
            self.rollback_called = True

        def refresh(self, obj):
            return None

    db = FakeDb()
    user = UserCreate(email=unique_email(), password="StrongPass1")

    with pytest.raises(RuntimeError, match="db unavailable"):
        create_user_route(user=user, db=db)

    assert db.rollback_called is True


def test_login_returns_both_tokens(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    r = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_with_valid_token(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    login_response = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    r = client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token
    assert data["token_type"] == "bearer"


def test_refresh_with_invalid_token_returns_401(client):
    r = client.post(
        "/api/v1/refresh",
        json={"refresh_token": "invalid_token_value"},
    )
    assert r.status_code == 401, r.text
    data = r.json()
    assert data["error"]["code"] == "refresh_token_invalid"


def test_logout_revokes_token(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    login_response = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    r = client.post(
        "/api/v1/logout",
        json={"refresh_token": refresh_token},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["message"] == "Successfully logged out"


def test_logout_with_invalid_token_returns_401(client):
    r = client.post(
        "/api/v1/logout",
        json={"refresh_token": "invalid_token_value"},
    )
    assert r.status_code == 401, r.text
    data = r.json()
    assert data["error"]["code"] == "refresh_token_invalid"


def test_refresh_token_not_usable_after_logout(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    login_response = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200

    r = client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r.status_code == 401, r.text
    data = r.json()
    assert data["error"]["code"] == "refresh_token_invalid"


def test_new_access_token_from_refresh_is_valid(client):
    email = unique_email()
    password = "StrongPass1"

    client.post("/api/v1/users", json={"email": email, "password": password})

    login_response = client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]

    auth_headers = {"Authorization": f"Bearer {new_access_token}"}
    r = client.get("/api/v1/me", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == email
