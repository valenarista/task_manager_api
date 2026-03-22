<p align="center">
  <a href="https://task-manager-api-s2ow.onrender.com/docs" rel="noopener">
 <img width=300px height=300px src="logo-taskmanagerapi.png" alt="Project logo"></a>
</p>

<h3 align="center">Task Manager API</h3>

<div align="center">

Backend REST API for task management built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, JWT authentication, automated tests, CI, and Render deployment.

</div>

---

<p align="center"> A backend portfolio project focused on authentication, authorization, testing, clean architecture, database migrations, containerization, and deployment.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Tech Stack](#tech-stack)
- [Live Demo](#live-demo)
- [Getting Started](#getting_started)
- [Running the tests](#-running-the-tests)
- [Usage](#usage)
- [Error Contract](#error-contract)
- [Error Reference](#error-reference)
- [Observability](#observability)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [Built Using](#built_using)
- [Authors](#authors)

## 🧐 About <a name = "about"></a>

Task Manager API is a RESTful backend service that allows users to register, authenticate, and manage their own tasks securely. The project was built as a backend engineering portfolio project with the goal of practicing real-world backend development concepts such as JWT-based authentication, per-user authorization, structured project architecture, testing, CI, database migrations, and deployment.

The API ensures that each user can only access and modify their own resources. It also includes pagination and filtering for task listing, Docker-based local development, Alembic-managed schema evolution, automated tests with Pytest, CI with GitHub Actions, and a live deployment on Render.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic
- JWT / OAuth2PasswordBearer
- Docker / Docker Compose
- Pytest
- GitHub Actions
- Render

## Live Demo

- API Base URL: `https://task-manager-api-s2ow.onrender.com/`
- Swagger Docs: `https://task-manager-api-s2ow.onrender.com/docs`

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

Make sure you have the following installed:

- Python 3.12+
- PostgreSQL
- Docker Desktop
- Git

You can verify some of them with:

```bash
python --version
docker --version
docker compose version
psql --version
```

### Installing

#### Option 1: Run with Docker (recommended)

Start the development environment:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Start the production-like local environment:

```bash
docker compose up --build
```

The API docs will be available at:

```text
http://localhost:8000/docs
```

#### Option 2: Run with a local Python environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements-dev.txt
```

Create a `.env` file based on `.env.example` and configure your local values.

Run database migrations:

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Once the server is running, open:

```text
http://localhost:8000/docs
```

You can then register a user, log in, authorize with Swagger, and start creating tasks.

## 🔧 Running the tests <a name = "tests"></a>

This project includes automated tests for authentication, authorization, pagination, filtering, and protected routes.

Run the full test suite with:

```bash
pytest
```

On Windows PowerShell, you can run tests with one command (it reuses `.venv`, installs dependencies if needed, and executes `pytest`):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

Pass specific pytest arguments:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -q tests\test_auth_and_tasks.py
```

### Break down into end to end tests

The tests simulate realistic user flows such as:

- user registration
- login and token retrieval
- accessing protected routes
- creating, listing, updating, and deleting tasks
- preventing one user from accessing another user's tasks

Example:

```bash
pytest tests/test_auth_and_tasks.py
```

### Quality checks (lint, types, coverage, hooks)

Run all quality checks with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality-check.ps1
```

The script runs:

- `ruff check .`
- `mypy app`
- `pytest --cov=app --cov-report=term-missing --cov-fail-under=90`
- `pre-commit run --all-files`

Optional (skip hooks):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality-check.ps1 -SkipPreCommit
```

Install git hooks once:

```bash
pre-commit install
```

## Contributing

Local quality baseline before opening a PR:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quality-check.ps1 -SkipPreCommit
```

This project expects:

- `ruff check .`
- `mypy app`
- `pytest --cov=app --cov-report=term-missing --cov-fail-under=90`

PRs use the repository template at `.github/pull_request_template.md` with a quality checklist.

Recommended branch protection on GitHub:

- Require the `CI / quality` check to pass before merge.

## 🎈 Usage <a name="usage"></a>

Typical usage flow:

1. Register a new user with `POST /api/v1/users`
2. Log in with `POST /api/v1/login`
3. Use the returned JWT access token to authorize requests
4. Access `GET /api/v1/me` to retrieve the current user
5. Create and manage tasks through the `/api/v1/tasks` endpoints

The task listing endpoint supports pagination and filtering:

```http
GET /api/v1/tasks?skip=0&limit=10&done=false
```

Example response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "Study FastAPI",
      "description": "Review dependency injection",
      "done": false
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

## Error Contract

All API errors follow a normalized JSON shape:

```json
{
  "error": {
    "code": "string_code",
    "message": "Human readable message",
    "details": []
  },
  "detail": "Human readable message"
}
```

`details` is optional and is mainly used for validation errors (`422`).

Common examples:

- Authentication missing: `error.code = "http_401"`
- Invalid token/credentials: `error.code = "invalid_credentials"`
- Duplicate email: `error.code = "email_already_registered"`
- Missing task: `error.code = "task_not_found"`
- Validation error: `error.code = "validation_error"`
- Unhandled server error: `error.code = "internal_error"`

## Error Reference

Main endpoint/status mapping:

| Endpoint | Status | Error Code | Message |
|---|---:|---|---|
| `POST /api/v1/users` | `409` | `email_already_registered` | `Email already registered` |
| `POST /api/v1/users` | `422` | `validation_error` | `Validation failed` |
| `POST /api/v1/login` | `400` | `invalid_credentials` | `Invalid email or password` |
| `POST /api/v1/login` | `422` | `validation_error` | `Validation failed` |
| `GET /api/v1/me` | `401` | `http_401` or `invalid_credentials` | `Not authenticated` or `Could not validate credentials` |
| `GET /api/v1/tasks` | `401` | `http_401` | `Not authenticated` |
| `GET /api/v1/tasks` | `422` | `validation_error` | `Validation failed` |
| `PATCH /api/v1/tasks/{task_id}` | `404` | `task_not_found` | `Task not found` |
| `DELETE /api/v1/tasks/{task_id}` | `404` | `task_not_found` | `Task not found` |
| Any endpoint | `500` | `internal_error` | `Internal server error` |

## Observability

The API uses request-scoped tracing with `X-Request-ID`.

- If the client sends `X-Request-ID`, the API preserves it.
- If the client does not send it, the API generates one.
- Every response includes `X-Request-ID` (success and error).
- Server logs include `request_id` so application logs and client errors can be correlated.

## 🚀 Deployment <a name = "deployment"></a>

The project is deployed on Render using:

- a PostgreSQL database service
- a FastAPI web service
- environment variables for configuration
- Alembic migrations executed during service startup

To deploy a similar setup:

1. Create a PostgreSQL database on Render
2. Create a Web Service connected to the GitHub repository
3. Set the required environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALGORITHM`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`
4. Use the following build and start commands:

```bash
pip install -r requirements.txt
```

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## ⛏️ Built Using <a name = "built_using"></a>

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [PostgreSQL](https://www.postgresql.org/) - Database
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [Docker](https://www.docker.com/) - Containerization
- [Pytest](https://pytest.org/) - Testing framework
- [GitHub Actions](https://github.com/features/actions) - Continuous Integration
- [Render](https://render.com/) - Deployment platform

## ✍️ Authors <a name = "authors"></a>

- **Valentin Arista** - Backend development, architecture, testing, Dockerization, CI, and deployment
