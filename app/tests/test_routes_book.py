import pytest
import random

from app.db_operations.dependencies import get_session
from app.db_operations.book import BookNotFound, create_book, read_book
from app.db_operations.user import create_user, read_user, UserNotFound
from app.main import app
from app.models.book import *
from app.models.user import *
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, StaticPool, SQLModel

existing_user_id = None
existing_book_id = None


def get_random_string(n=10):
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


@pytest.fixture(name="regular_token", scope="module")
def regular_token_fixture(session: Session, client: TestClient):
    try:
        read_user(session, username="fixture-regular-user")
    except UserNotFound:
        create_user(
            session,
            UserCreate(
                username="fixture-regular-user",
                password="password",
                role=USER_ROLE.REGULAR_USER,
            ),
        )

    post_response = client.post(
        "/users/login",
        data={"username": "fixture-regular-user", "password": "password"},
    )
    return post_response.json()["access_token"]


def test_create_books_returns_401_when_no_valid_auth_token_included(
    session: Session, client: TestClient
):
    user = create_user(
        session, UserCreate(username="test-auth", password="test", role=USER_ROLE.ADMIN)
    )
    post_response = client.post(
        "/books",
        json={
            "title": "this-book-shouldnt-exist",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(user.id),
            "isbn": "1111111111",
        },
    )
    assert post_response.status_code == 401


def test_create_books_successfully_adds_valid_book(
    session: Session, client: TestClient
):
    global existing_user_id
    global existing_book_id
    user = create_user(
        session, UserCreate(username="test", password="test", role=USER_ROLE.ADMIN)
    )
    post_response = client.post(
        "/users/login", data={"username": "test-auth", "password": "test"}
    )
    assert post_response.status_code == 200
    token = post_response.json()["access_token"]

    post_response = client.post(
        "/books",
        json={
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(user.id),
            "isbn": "1111111111",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(user.id)
    existing_user_id = user.id
    existing_book_id = post_response.json()["id"]


def test_create_books_returns_401_when_trying_to_add_book_to_other_user(
    session: Session, client: TestClient, regular_token: str
):
    random_username = get_random_string(100)
    other_user = create_user(
        session,
        user=UserCreate(
            username=random_username,
            password="password",
            role=USER_ROLE.REGULAR_USER,
        ),
    )

    post_response = client.post(
        "/books",
        json={
            "title": "a",
            "visibility_to_others": "true",
            "rating": "1",
            "user_id": str(other_user.id),
            "isbn": "1111111111",
        },
        headers={"Authorization": f"Bearer {regular_token}"},
    )

    assert post_response.status_code == 401
    assert "Not authorized" in post_response.json()["detail"]


def test_read_books_user_id_returns_401_when_no_valid_auth_token_included(
    client: TestClient,
):
    get_response = client.get(f"/books/{existing_user_id}")
    assert get_response.status_code == 401


def test_read_books_user_id_successfully_reads_all_books_for_a_user(client: TestClient):
    global existing_user_id
    post_response = client.post(
        "/users/login", data={"username": "test", "password": "test"}
    )
    token = post_response.json()["access_token"]

    client.post(
        "/books",
        json={
            "title": "book2",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(existing_user_id),
            "isbn": "1111111111",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    get_response = client.get(
        f"/books/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    print(get_response.json())
    assert get_response.status_code == 200
    assert get_response.json()[0]["title"] == "book1"
    assert get_response.json()[1]["title"] == "book2"


def test_read_books_user_id_requested_by_regular_user_for_other_user_lists_only_books_with_visibility_to_others_true(
    session: Session, client: TestClient, regular_token: str
):
    random_username = get_random_string(100)
    other_user = create_user(
        session,
        user=UserCreate(
            username=random_username,
            password="password",
            role=USER_ROLE.REGULAR_USER,
        ),
    )
    post_response = client.post(
        "/users/login", data={"username": random_username, "password": "password"}
    )
    assert post_response.status_code == 200
    token = post_response.json()["access_token"]

    post_response = client.post(
        "/books",
        json={
            "title": "a",
            "visibility_to_others": "true",
            "rating": "1",
            "user_id": str(other_user.id),
            "isbn": "1111111111",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post_response.status_code == 200

    post_response = client.post(
        "/books",
        json={
            "title": "b",
            "visibility_to_others": "false",
            "rating": "1",
            "user_id": str(other_user.id),
            "isbn": "1111111111",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post_response.status_code == 200

    get_response = client.get(
        f"/books/{other_user.id}", headers={"Authorization": f"Bearer {regular_token}"}
    )
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1
    assert get_response.json()[0]["title"] == "a"


def test_read_books_returns_401_when_no_valid_auth_token_included(
    session: Session, client: TestClient
):
    res = client.get("/books")
    assert res.status_code == 401


def test_read_books_successfully_reads_all_books(session: Session, client: TestClient):
    post_response = client.post(
        "/users/login", data={"username": "test", "password": "test"}
    )
    token = post_response.json()["access_token"]
    # Adding another user and book to have at least two
    new_user = create_user(
        session,
        UserCreate(username="test2", password="test2", role=USER_ROLE.REGULAR_USER),
    )

    random_book_name_1 = get_random_string(100)
    create_book(
        session,
        BookCreate(
            title=random_book_name_1,
            rating=1,
            visibility_to_others=False,
            user_id=new_user.id,
        ),
    )

    random_book_name_2 = get_random_string(100)
    create_book(
        session,
        BookCreate(
            title=random_book_name_2,
            rating=1,
            visibility_to_others=False,
            user_id=new_user.id,
        ),
    )

    res = client.get("/books", headers={"Authorization": f"Bearer {token}"})
    books = list(
        filter(
            lambda book: book["title"] in [random_book_name_1, random_book_name_2],
            res.json(),
        )
    )
    assert len(books) == 2


def test_update_books_book_id_successfully_updates_an_existing_book(
    session: Session, client: TestClient
):
    global existing_book_id
    patch_response = client.patch(
        f"/books/{existing_book_id}", json={"title": "book-1", "author": "john doe"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "book-1"
    assert patch_response.json()["author"] == "john doe"


def test_update_books_book_id_successfully_updates_an_existing_book_with_user_id(
    session: Session, client: TestClient
):
    global existing_book_id
    new_user = create_user(
        session,
        UserCreate(username="test3", password="test3", role=USER_ROLE.REGULAR_USER),
    )
    patch_response = client.patch(
        f"/books/{existing_book_id}", json={"user_id": str(new_user.id)}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["user_id"] == str(new_user.id)


def test_delete_books_book_id_successfully_deletes_an_existing_book(
    session: Session, client: TestClient
):
    global existing_book_id
    delete_response = client.delete(f"/books/{existing_book_id}")
    assert delete_response.status_code == 200
    assert delete_response.text == "OK"
    with pytest.raises(BookNotFound):
        read_book(session, id=uuid.UUID(existing_book_id))


def test_delete_books_book_id_raises_exception_for_non_existing_book(
    client: TestClient,
):
    delete_response = client.delete(f"/books/{uuid.uuid4()}")
    assert delete_response.status_code == 404
