import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.task import Task
from app.models.user import User

_ = (User, Task, RefreshToken)

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def unique_email():
    return f"user_{uuid.uuid4().hex[:12]}@example.com"
