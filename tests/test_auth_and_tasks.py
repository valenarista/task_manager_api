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