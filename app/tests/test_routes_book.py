import pytest

from app.db_operations.dependencies import get_session
from app.db_operations.book import BookNotFound, create_book, read_book
from app.db_operations.user import create_user
from app.main import app
from app.models.book import *
from app.models.user import *
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


# TODO: Uncomment when auth implemented for this route
# def test_create_books_returns_401_when_no_valid_auth_token_included(session: Session, client: TestClient):
#     user = create_user(
#         session, UserCreate(username="test-auth", password="test", role=USER_ROLE.ADMIN)
#     )
#     post_response = client.post(
#         "/books",
#         json={
#             "title": "this-book-shouldnt-exist",
#             "rating": 5,
#             "visibility_to_others": True,
#             "user_id": str(user.id),
#             "isbn": "1111111111",
#         },
#     )
#     assert post_response.status_code == 401

def test_create_books_successfully_adds_valid_book(session: Session, client: TestClient):
    global existing_user_id
    global existing_book_id
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
    assert post_response.status_code == 200
    assert post_response.json()["title"] == "book1"
    assert post_response.json()["rating"] == 5
    assert post_response.json()["user_id"] == str(user.id)
    existing_user_id = user.id
    existing_book_id = post_response.json()["id"]

def test_read_books_user_id_successfully_reads_all_books_for_a_user(client: TestClient):
    global existing_user_id
    client.post(
        "/books",
        json={
            "title": "book2",
            "rating": 5,
            "visibility_to_others": True,
            "user_id": str(existing_user_id),
            "isbn": "1111111111",
        },
    )

    get_response = client.get(f"/books/{existing_user_id}")
    assert get_response.status_code == 200
    print(get_response.json())
    assert get_response.json()[0]["title"] == "book1"
    assert get_response.json()[1]["title"] == "book2"

def test_read_books_successfully_reads_all_books(session: Session, client: TestClient):
    # Adding another user and book to have at least two
    new_user = create_user(session, UserCreate(username="test2", password="test2", role=USER_ROLE.REGULAR_USER))
    new_book = create_book(session, BookCreate(title="book3", rating=1, visibility_to_others=False, user_id=new_user.id))
    res = client.get("/books")
    assert res.json()[0]["title"] == "book1"
    assert res.json()[1]["title"] == "book2"
    assert res.json()[2]["title"] == "book3"

def test_update_books_book_id_successfully_updates_an_existing_book(session: Session, client: TestClient):
    global existing_book_id
    put_response = client.put(f"/books/{existing_book_id}", json={"title": "book-1", "author":"john doe"})
    assert put_response.status_code == 200
    assert put_response.json()["title"] == "book-1"
    assert put_response.json()["author"] == "john doe"

def test_update_books_book_id_successfully_updates_an_existing_book_with_user_id(session: Session, client: TestClient):
    global existing_book_id
    new_user = create_user(session, UserCreate(username="test3", password="test3", role=USER_ROLE.REGULAR_USER))
    put_response = client.put(f"/books/{existing_book_id}", json={"user_id": str(new_user.id)})
    assert put_response.status_code == 200
    assert put_response.json()["user_id"] == str(new_user.id)

def test_delete_books_book_id_successfully_deletes_an_existing_book(session: Session, client: TestClient):
    global existing_book_id
    delete_response = client.delete(f"/books/{existing_book_id}")
    assert delete_response.status_code == 200
    assert delete_response.text == "OK"
    with pytest.raises(BookNotFound):
        read_book(session, id=uuid.UUID(existing_book_id))

def test_delete_books_book_id_raises_exception_for_non_existing_book(client: TestClient):
    delete_response = client.delete(f"/books/{uuid.uuid4()}")
    assert delete_response.status_code == 404

