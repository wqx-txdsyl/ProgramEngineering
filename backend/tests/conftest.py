import os

os.environ.setdefault("JWT_SECRET_KEY", "pytest-secret-key-00000000000000000000000000")

import itertools
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import models
from app.database import get_session
from app.main import app
from app.models import PointAccount, PointTransaction, User
from app.services.auth import hash_password

TEST_PASSWORD = "password123"


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine):
    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client, engine) -> Callable[..., dict]:
    counter = itertools.count(1)

    def _make(role: str = "student", username: str | None = None) -> dict:
        username = username or f"{role}_{next(counter)}"
        with Session(engine) as session:
            session.add(User(
                username=username,
                password_hash=hash_password(TEST_PASSWORD),
                role=role,
            ))
            session.commit()
            user_id = session.exec(
                select(User).where(User.username == username)
            ).one().id

        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200, response.text

        return {
            "id": user_id,
            "username": username,
            "role": role,
            "headers": {"Authorization": f"Bearer {response.json()['access_token']}"},
        }

    return _make


@pytest.fixture
def make_task(client) -> Callable[..., int]:
    def _make(teacher_headers: dict, title: str = "学习任务") -> int:
        response = client.post(
            "/api/tasks",
            json={"title": title},
            headers=teacher_headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    return _make


@pytest.fixture
def give_points(engine) -> Callable[..., None]:
    counter = itertools.count(1)

    def _give(user_id: int, amount: int) -> None:
        with Session(engine) as session:
            account = session.exec(
                select(PointAccount).where(PointAccount.user_id == user_id)
            ).first()
            if account is None:
                session.add(PointAccount(user_id=user_id, balance=0))
                session.flush()

            from sqlalchemy import update

            session.execute(
                update(PointAccount)
                .where(PointAccount.user_id == user_id)
                .values(balance=PointAccount.balance + amount)
            )
            session.add(PointTransaction(
                user_id=user_id,
                change=amount,
                source_type="grant",
                source_id=next(counter),
            ))
            session.commit()

    return _give
