import pytest

from app.db_operations.dependencies import get_session
from app.db_operations.user import create_user
from app.main import app
from app.models.book import *
from app.models.user import *
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, StaticPool, SQLModel

existing_user_id = None

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

def test_create_users_successfully_adds_valid_user(client: TestClient):
    global existing_user_id
    post_response = client.post("/users", json={"username": "test-1", "password": "pass-1", "role": "ADMIN"})
    assert post_response.status_code == 200
    assert post_response.json()["username"] == "test-1"
    assert post_response.json()["role"] == "ADMIN"
    existing_user_id = post_response.json()["id"]

def test_read_all_users_successfully_returns_all_users(session: Session, client: TestClient):
    create_user(session, user=UserCreate(username="test-2", password="pass-2", role=USER_ROLE.ADMIN))
    get_response = client.get("/users")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 2
    assert get_response.json()[0]["username"] == "test-1"
    assert get_response.json()[1]["username"] == "test-2"

def test_read_user_user_id_successfully_reads_valid_user(client: TestClient):
    global existing_user_id
    get_response = client.get(f"/users/{existing_user_id}")
    assert get_response.status_code == 200
    assert str(get_response.json()["id"]) == str(existing_user_id)
    assert get_response.json()["username"] == "test-1"
    assert get_response.json()["role"] == "ADMIN"

def test_update_users_user_id_successfully_updates_an_existing_user(client: TestClient):
    global existing_user_id
    put_response = client.put(f"/users/{existing_user_id}", json={"username": "test-new-1"})
    assert put_response.status_code == 200
    assert put_response.json()["id"] == str(existing_user_id)
    assert put_response.json()["username"] == "test-new-1"

# Add test case for following other users
