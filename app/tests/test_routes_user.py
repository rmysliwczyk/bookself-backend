import pytest
import random

from app.db_operations.dependencies import get_session
from app.db_operations.user import create_user, delete_user, read_user, UserNotFound
from app.main import app
from app.models.book import *
from app.models.user import *
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, StaticPool, SQLModel

existing_user_id = None


def get_random_username(n=10):
    return "".join([chr(random.randrange(65, 91)) for _ in range(n)])


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


@pytest.fixture(name="token", scope="module")
def token_fixture(session: Session, client: TestClient):
    try:
        read_user(session, username="fixture-user")
    except UserNotFound:
        create_user(
            session,
            UserCreate(
                username="fixture-user", password="password", role=USER_ROLE.ADMIN
            ),
        )

    post_response = client.post(
        "/users/login", data={"username": "fixture-user", "password": "password"}
    )
    return post_response.json()["access_token"]

@pytest.fixture(name="regular_token", scope="module")
def regular_token_fixture(session: Session, client: TestClient):
    try:
        read_user(session, username="fixture-regular-user")
    except UserNotFound:
        create_user(
            session,
            UserCreate(
                username="fixture-regular-user", password="password", role=USER_ROLE.REGULAR_USER
            ),
        )

    post_response = client.post(
        "/users/login", data={"username": "fixture-regular-user", "password": "password"}
    )
    return post_response.json()["access_token"]

def test_create_users_successfully_adds_valid_user(client: TestClient, token: str):
    global existing_user_id
    post_response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "test-1", "password": "pass-1", "role": "ADMIN"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["username"] == "test-1"
    assert post_response.json()["role"] == "ADMIN"
    existing_user_id = post_response.json()["id"]


def test_read_all_users_successfully_returns_all_users(
    session: Session, client: TestClient, token: str
):
    create_user(
        session,
        user=UserCreate(username="test-2", password="pass-2", role=USER_ROLE.ADMIN),
    )
    get_response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 200
    assert len(get_response.json()) == 3
    assert get_response.json()[0]["username"] == "fixture-user"
    assert get_response.json()[1]["username"] == "test-1"
    assert get_response.json()[2]["username"] == "test-2"


def test_read_user_user_id_successfully_reads_valid_user(
    client: TestClient, token: str
):
    global existing_user_id
    get_response = client.get(
        f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    assert str(get_response.json()["id"]) == str(existing_user_id)
    assert get_response.json()["username"] == "test-1"
    assert get_response.json()["role"] == "ADMIN"


def test_read_user_user_id_returns_404_if_user_doesnt_exist(
    client: TestClient, token: str
):
    get_response = client.get(
        f"/users/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_update_users_user_id_successfully_updates_an_existing_user(
    client: TestClient, token: str
):
    global existing_user_id
    patch_response = client.patch(
        f"/users/{existing_user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "test-new-1"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["id"] == str(existing_user_id)
    assert patch_response.json()["username"] == "test-new-1"


def test_update_users_user_id_successfully_updates_an_existing_user_to_add_followed_user(
    session: Session, client: TestClient, token: str
):
    global existing_user_id
    second_existing_user = read_user(session, username="test-2")
    patch_response = client.patch(
        f"/users/{existing_user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"following_ids": [str(second_existing_user.id)]},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["id"] == str(existing_user_id)
    assert len(patch_response.json()["following"]) == 1
    assert patch_response.json()["following"][0]["username"] == "test-2"


def test_update_users_user_id_returns_404_if_user_doesnt_exist(
    client: TestClient, token: str
):
    patch_response = client.patch(
        f"/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "madeup"},
    )
    assert patch_response.status_code == 404


def test_read_user_user_id_successfully_returns_user_with_following(
    client: TestClient, token: str
):
    global existing_user_id
    get_response = client.get(
        f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["following"][0]["username"] == "test-2"


def test_read_user_user_id_successfully_returns_user_with_followers(
    session: Session, client: TestClient, token: str
):
    global existing_user_id
    second_existing_user = read_user(session, username="test-2")
    get_response = client.get(
        f"/users/{str(second_existing_user.id)}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["followers"][0]["username"] == "test-new-1"


def test_update_users_user_id_successfully_removes_all_followed_users(
    client: TestClient, token: str
):
    global existing_user_id
    patch_response = client.patch(
        f"/users/{existing_user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"following_ids": []},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["id"] == str(existing_user_id)
    assert len(patch_response.json()["following"]) == 0
    get_response = client.get(
        f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(get_response.json()["following"]) == 0


def test_read_user_user_id_successfully_returns_user_with_book_information_included(
    client: TestClient, token: str
):
    global existing_user_id
    client.post(
        "/books",
        json={
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(existing_user_id),
            "isbn": "1111111111",
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    get_response = client.get(
        f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["books"][0]["title"] == "book1"


def test_delete_user_user_id_successfully_deletes_an_existing_user(
        session: Session, client: TestClient, token: str
):
    global existing_user_id
    delete_response = client.delete(f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_response.status_code == 200
    with pytest.raises(UserNotFound):
        read_user(session, id=uuid.UUID(existing_user_id))


def test_read_users_me_successfully_returns_information_about_token_owner(
    client: TestClient, token: str
):
    get_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 200
    assert get_response.json()["username"] == "fixture-user"


def test_update_users_user_id_successfully_updates_an_existing_regular_user_for_self_request(
    session: Session, client: TestClient, token: str
):
    user = create_user(
        session,
        user=UserCreate(
            username="regular-user",
            password="regular-user-password",
            role=USER_ROLE.REGULAR_USER,
        ),
    )
    post_response = client.post(
        "/users/login",
        data={"username": "regular-user", "password": "regular-user-password"},
    )
    patch_response = client.patch(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {post_response.json()['access_token']}"},
        json={"username": "regular-user-changed"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["id"] == str(user.id)
    assert patch_response.json()["username"] == "regular-user-changed"


def test_create_user_returns_error_for_non_unique_username(
    client: TestClient, token: str
):
    random_username = get_random_username(100)
    client.post(
        "/users",
        json={"username": random_username, "password": "password", "role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )
    post_response = client.post(
        "/users",
        json={"username": random_username, "password": "password", "role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(post_response.json())
    assert post_response.status_code == 400
    assert "already exists" in post_response.json()["detail"]


def test_update_user_returns_401_when_regular_user_tries_updating_other_user(
    client: TestClient,
):
    random_username = get_random_username(100)
    other_random_username = get_random_username(100)
    user_id = None
    other_user_id = None

    post_response = client.post(
        "/users",
        json={
            "username": random_username,
            "password": "password",
            "role": "REGULAR_USER",
        },
    )
    assert post_response.status_code == 200
    user_id = post_response.json()["id"]

    post_response = client.post(
        "/users",
        json={
            "username": other_random_username,
            "password": "password",
            "role": "REGULAR_USER",
        },
    )
    assert post_response.status_code == 200
    other_user_id = post_response.json()["id"]

    post_response = client.post(
        "/users/login", data={"username": random_username, "password": "password"}
    )
    regular_user_token = post_response.json()["access_token"]

    patch_response = client.patch(
        f"/users/{other_user_id}",
        json={"following_ids": [user_id]},
        headers={"Authorization": f"Bearer {regular_user_token}"},
    )

    assert patch_response.status_code == 401
    assert (
        "Not authorized" in patch_response.json()["detail"]
    )

def test_delete_user_id_returns_401_if_called_by_other_regular_user(client: TestClient, token: str, regular_token: str):
    random_username = get_random_username(100)
    post_response = client.post(
        "/users",
        json={"username": random_username, "password": "password", "role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert post_response.status_code == 200

    delete_response = client.delete(f"/users/{post_response.json()['id']}", headers={"Authorization": f"Bearer {regular_token}"})

    assert delete_response.status_code == 401


