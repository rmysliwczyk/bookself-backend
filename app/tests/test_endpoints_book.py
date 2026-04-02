import pytest

from app.db_operations.dependencies import get_session
from app.db_operations.user import create_user
from app.main import app
from app.models.book import *
from app.models.user import *
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, StaticPool, SQLModel


@pytest.fixture(name="session", scope="module")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", scope="module")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_books_correctly_adds_valid_book(session: Session, client: TestClient):
    user = create_user(
        session, UserCreate(username="test", password="test", role=USER_ROLE.ADMIN)
    )
    post_response = client.post(
        "/books",
        json={
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(user.id),
            "isbn": "1111111111",
        },
    )
    print(post_response.json())
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(user.id)
