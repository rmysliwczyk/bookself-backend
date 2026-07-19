import base64
import json
import pytest
import pathlib

from app.db_operations.dependencies import get_session
from app.db_operations.book import BookNotFound, create_book, read_book
from app.db_operations.user import create_user, read_user, UserNotFound
from app.main import app
from app.models.book import *
from app.models.user import *
from app.settings import Settings
from app.tests.helper_functions import get_random_string
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, StaticPool, SQLModel

existing_user_id = None
existing_book_id = None


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
    except UserNotFound: #pragma: no cover
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
    except UserNotFound: #pragma: no cover
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


@pytest.fixture(name="regular_user", scope="module")
def regular_user_data_fixture(session: Session, client: TestClient) -> UserPublic:
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

    data = post_response.json()["user"]
    del data["hashed_password"]
    return UserPublic.model_validate(data)

@pytest.fixture(name="test_image", scope="module")
def test_image_fixture() -> bytes:
    script_dir_filepath = pathlib.Path(__file__).parent
    test_image = None
    with open(script_dir_filepath/"test_cover_image.jpg", "rb") as f:
        test_image = f.read()

    return test_image

@pytest.fixture(name="test_image_png", scope="module")
def test_image_fixture_png() -> bytes:
    script_dir_filepath = pathlib.Path(__file__).parent
    test_image = None
    with open(script_dir_filepath/"test_cover_image.png", "rb") as f:
        test_image = f.read()

    return test_image

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
        client: TestClient, regular_user: User, regular_token: str, test_image: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(regular_user.id)


def test_create_books_returns_401_when_trying_to_add_book_to_other_user(
        session: Session, client: TestClient, regular_token: str, test_image: bytes
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

    data = json.dumps({
            "title": "a",
            "visibility_to_others": "true",
            "rating": "1",
            "user_id": str(other_user.id),
            "isbn": "1111111111",
        })

    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )

    assert post_response.status_code == 401
    assert "Not authorized" in post_response.json()["detail"]


def test_read_books_returns_401_when_no_valid_auth_token_included(
    session: Session, client: TestClient
):
    res = client.get("/books")
    assert res.status_code == 401


def test_read_books_successfully_reads_all_books(session: Session, client: TestClient, token: str):
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

    res = client.delete(f"/users/{new_user.id}", headers={"Authorization" : f"Bearer {token}"})
    assert res.status_code == 200


def test_update_books_book_id_successfully_updates_an_existing_book(
        session: Session, client: TestClient, regular_user: User, regular_token: str, test_image: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200

    patch_response = client.patch(
            f"/books/{post_response.json()['id']}", json={"title": "book-1", "author": "john doe"}, headers={"Authorization": f"Bearer {regular_token}"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "book-1"
    assert patch_response.json()["author"] == "john doe"


def test_update_books_book_id_fails_updating_an_existing_book_with_other_user_id(
        session: Session, client: TestClient, regular_user: User, regular_token: str, test_image: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})

    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200

    random_uuid = str(uuid.uuid4())
    patch_response = client.patch(
            f"/books/{post_response.json()['id']}", json={"user_id": str(random_uuid)}, headers={"Authorization": f"Bearer {regular_token}"}
    )
    assert patch_response.status_code == 400
    assert "Cannot assign books to other users" in patch_response.json()["detail"]


def test_delete_books_book_id_successfully_deletes_an_existing_book(
        session: Session, client: TestClient, regular_token: str, regular_user: User, test_image: bytes
):
    
    data = json.dumps({
            "title": "book-to-be-deleted",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})

    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200

    delete_response = client.delete(f"/books/{post_response.json()['id']}")
    assert delete_response.status_code == 200
    assert delete_response.text == "OK"
    with pytest.raises(BookNotFound):
        read_book(session, id=uuid.UUID(post_response.json()['id']))


def test_delete_books_book_id_raises_exception_for_non_existing_book(
    client: TestClient,
):
    delete_response = client.delete(f"/books/{uuid.uuid4()}")
    assert delete_response.status_code == 404

def test_create_book_raises_validation_error_for_incorrect_image_format(
        client: TestClient, regular_user: User, regular_token: str, test_image: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.img", test_image, "image/img")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )

    assert post_response.status_code == 422
    assert "Invalid image format" in post_response.json()["detail"]

def test_create_books_successfully_adds_valid_book_when_using_png(
        client: TestClient, regular_user: User, regular_token: str, test_image_png: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.png", test_image_png, "image/png")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(regular_user.id)

def test_create_books_raises_validation_error_when_title_is_missing(
        client: TestClient, regular_user: User, regular_token: str, test_image: bytes
):
    data = json.dumps({
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.jpg", test_image, "image/jpeg")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 422
    assert "title" in post_response.json()["detail"][0]['loc']

def test_cover_picture_can_be_retrieved(
        client: TestClient, regular_user: User, regular_token: str, test_image_png: bytes
):
    data = json.dumps({
            "title": "book1",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(regular_user.id),
            "isbn": "1111111111"})
    post_response = client.post(
        "/books",
        data={"data": data},
        files={"cover_picture": ("test.png", test_image_png, "image/png")},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(regular_user.id)

    settings = Settings()
    filename = post_response.json()['cover_photo_url'].split("/")[-1]
    request_url = f"/books/{settings.media_base_url}?filename={filename}"
    get_response = client.get(request_url)
    assert get_response.status_code == 200
