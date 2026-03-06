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
    tasks = r.json()
    assert isinstance(tasks, list)
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
    tasks_2 = r.json()
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