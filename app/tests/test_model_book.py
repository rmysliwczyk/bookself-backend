# Testing pydantic validation for User model
import pytest
import uuid

from app.db_operations.book import BookNotFound, create_book, read_book, update_book, delete_book
from app.models.book import (
    MAX_TITLE_LENGTH,
    MAX_REVIEW_LENGTH,
    BaseBook,
    Book,
    BookCreate,
    BookPublic,
    BookUpdate,
)

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import create_engine, Session, select, SQLModel
from typing import Annotated


# Pydantic models validation tests
## BaseBook
def test_base_book_model_validation_successful_with_correct_required_fields():
    new_base_book = BaseBook(title="book_title", rating=10, visibility_to_others=True)
    assert new_base_book.title == "book_title"
    assert new_base_book.rating == 10
    assert new_base_book.visibility_to_others == True


def test_base_book_model_validation_successful_with_correct_required_and_optional_fields():
    new_base_book = BaseBook(
        title="book_title",
        rating=10,
        visibility_to_others=True,
        review="that was a good book",
    )
    assert new_base_book.title == "book_title"
    assert new_base_book.rating == 10
    assert new_base_book.visibility_to_others == True
    assert new_base_book.review == "that was a good book"


def test_base_book_model_validation_fails_with_extra_fields():
    with pytest.raises(ValidationError) as exc:
        BaseBook(title="book_title", rating=10, visibility_to_others=True, used=True)  # type: ignore
    assert "used\n  Extra inputs are not permitted" in str(exc.value)


def test_base_book_model_validation_fails_with_missing_required_fields():
    with pytest.raises(ValidationError) as exc:
        BaseBook(title="book_title", rating=10)  # type: ignore
    assert "visibility_to_others\n  Field required" in str(exc.value)


def test_base_book_mode_validation_fails_with_incorrect_fields():
    with pytest.raises(ValidationError) as exc:
        BaseBook(name="book_title", grade=10, is_visible=True)  # type: ignore
    assert "title\n  Field required" in str(exc.value)
    assert "rating\n  Field required" in str(exc.value)
    assert "visibility_to_others\n  Field required" in str(exc.value)


## BookCreate
def test_book_create_model_validation_successful_with_correct_required_fields():
    book_creation_data = BookCreate(
        title="book_title", rating=10, visibility_to_others=True
    )
    assert book_creation_data.title == "book_title"
    assert book_creation_data.rating == 10
    assert book_creation_data.visibility_to_others == True


def test_book_create_model_validation_successful_with_correct_required_and_optional_fields():
    book_creation_data = BookCreate(
        title="book_title",
        rating=10,
        visibility_to_others=True,
        review="that was a good book",
        cover_photo_url="http://example.com/cover.jpg",  # type: ignore
        isbn="9781566199094",  # type: ignore
    )
    assert book_creation_data.title == "book_title"
    assert book_creation_data.rating == 10
    assert book_creation_data.visibility_to_others == True
    assert book_creation_data.review == "that was a good book"
    assert str(book_creation_data.cover_photo_url) == "http://example.com/cover.jpg"
    assert book_creation_data.isbn == "9781566199094"


def test_book_create_model_validation_fails_with_extra_fields():
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10, visibility_to_others=True, used=True)  # type: ignore
    assert "used\n  Extra inputs are not permitted" in str(exc.value)


def test_book_create_model_validation_fails_with_missing_required_fields():
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10)  # type: ignore
    assert "visibility_to_others\n  Field required" in str(exc.value)


def test_book_create_mode_validation_fails_with_incorrect_fields():
    with pytest.raises(ValidationError) as exc:
        BookCreate(name="book_title", grade=10, is_visible=True)  # type: ignore
    assert "title\n  Field required" in str(exc.value)
    assert "rating\n  Field required" in str(exc.value)
    assert "visibility_to_others\n  Field required" in str(exc.value)


def test_book_create_model_validation_fails_with_rating_greater_than_10():
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=11, visibility_to_others=True)
    assert "rating\n  Input should be less than or equal to 10" in str(exc.value)


def test_book_create_model_validation_fails_with_rating_less_than_0():
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=-1, visibility_to_others=True)
    assert "rating\n  Input should be greater than or equal to 1" in str(exc.value)


def test_book_create_model_validation_fails_with_title_longer_than_max_length():
    title = "A" * MAX_TITLE_LENGTH + "A"
    with pytest.raises(ValidationError) as exc:
        BookCreate(title=title, rating=10, visibility_to_others=True)
    assert f"title\n  String should have at most {MAX_TITLE_LENGTH}" in str(exc.value)


def test_book_create_model_validation_fails_with_review_longer_than_max_length():
    review = "A" * MAX_REVIEW_LENGTH + "A"
    with pytest.raises(ValidationError) as exc:
        BookCreate(
            title="book_title", rating=10, visibility_to_others=True, review=review
        )
    assert f"review\n  String should have at most {MAX_REVIEW_LENGTH}" in str(exc.value)


def test_book_create_model_validation_fails_with_incorrect_cover_photo_url():
    url = "abcd"
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10, visibility_to_others=True, cover_photo_url=url)  # type: ignore
    assert "cover_photo_url\n  Input should be a valid URL" in str(exc.value)


def test_book_create_model_validation_fails_with_too_long_isbn():
    too_long_isbn = "97815661990941"
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10, visibility_to_others=True, isbn=too_long_isbn)  # type: ignore
    assert "isbn\n  Length for ISBN must be 10 or 13 digits" in str(exc.value)


def test_book_create_model_validation_fails_with_too_short_isbn():
    too_long_isbn = "978156619909"
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10, visibility_to_others=True, isbn=too_long_isbn)  # type: ignore
    assert "isbn\n  Length for ISBN must be 10 or 13 digits" in str(exc.value)


def test_book_create_model_validation_fails_with_incorrect_isbn():
    too_long_isbn = "1111111110"
    with pytest.raises(ValidationError) as exc:
        BookCreate(title="book_title", rating=10, visibility_to_others=True, isbn=too_long_isbn)  # type: ignore
    assert "isbn\n  Provided digit is invalid" in str(exc.value)


## BookPublic
def test_book_public_model_validation_successful_with_correct_fields():
    generated_uuid = uuid.uuid4()
    book_public_data = BookPublic(id=generated_uuid, title="book_title", rating=10, visibility_to_others=True)  # type: ignore
    assert book_public_data.id == generated_uuid
    assert book_public_data.title == "book_title"
    assert book_public_data.rating == 10
    assert book_public_data.visibility_to_others == True


## BookUpdate
def test_book_update_model_validation_successful_with_correct_fields_partial_fields_from_normally_required():
    book_update_data = BookUpdate(title="updated_title", rating=10)
    assert book_update_data.title == "updated_title"
    assert book_update_data.rating == 10


def test_book_update_model_validation_successful_with_correct_fields_all_fields_from_normally_required():
    book_update_data = BookUpdate(
        title="updated_title", rating=10, visibility_to_others=False
    )
    assert book_update_data.title == "updated_title"
    assert book_update_data.rating == 10
    assert book_update_data.visibility_to_others == False


def test_book_update_model_validation_successful_with_correct_fields_partial_fields_from_normally_optional():
    book_update_data = BookUpdate(review="some updated review", cover_photo_url="http://example.com")  # type: ignore
    assert book_update_data.review == "some updated review"
    assert str(book_update_data.cover_photo_url) == "http://example.com/"


def test_book_update_model_validation_successful_with_correct_fields_all_fields_from_normally_optional():
    book_update_data = BookUpdate(review="some updated review", cover_photo_url="http://example.com", isbn="9781566199094")  # type: ignore
    assert book_update_data.review == "some updated review"
    assert str(book_update_data.cover_photo_url) == "http://example.com/"
    assert book_update_data.isbn == "9781566199094"


## Book - Only a limited non-failure test due: #https://github.com/fastapi/sqlmodel/issues/453 Why does a SQLModel class with table=True not validate data ?
def test_book_model_validation_successful_with_correct_required_fields():
    generated_id = uuid.uuid4()
    new_book = Book(
        id=generated_id, title="table_book", rating=7, visibility_to_others=True
    )
    assert new_book.title == "table_book"
    assert new_book.rating == 7
    assert new_book.visibility_to_others == True


# Database operations tests

engine_url = "sqlite:///"
engine = create_engine(engine_url)
SQLModel.metadata.create_all(engine)

existing_book_id = None


## Book - Create
def test_create_book_creates_book_with_correct_fields():
    global existing_book_id
    with Session(engine) as session:
        create_book(session, BookCreate(title="book1", rating=5, visibility_to_others=True, isbn="1111111111"))  # type: ignore
        new_book_from_db = session.exec(select(Book).where(Book.title == "book1")).one()
        assert new_book_from_db.title == "book1"
        assert new_book_from_db.rating == 5
        assert new_book_from_db.visibility_to_others == True
        existing_book_id = new_book_from_db.id


## Book - Read
def test_read_book_by_title_returns_existing_book():
    global existing_book_id
    with Session(engine) as session:
        book_from_db = read_book(session, title="book1")
        assert book_from_db != None
        assert book_from_db.title == "book1"
        assert book_from_db.rating == 5
        assert book_from_db.visibility_to_others == True
        assert book_from_db.id == existing_book_id


def test_read_book_by_id_returns_existing_book():
    global existing_book_id
    with Session(engine) as session:
        book_from_db = read_book(session, id=existing_book_id)
        assert book_from_db != None
        assert book_from_db.title == "book1"
        assert book_from_db.rating == 5
        assert book_from_db.visibility_to_others == True
        assert book_from_db.id == existing_book_id


def test_read_book_by_title_raises_BookNotFound_when_book_not_found():
    with Session(engine) as session:
        with pytest.raises(BookNotFound) as exc:
            read_book(session, title="no_such_book")
        assert "Book no_such_book not found." in str(exc.value)

def test_read_book_by_id_raises_BookNotFound_when_book_not_found():
    random_uuid = uuid.uuid4()
    with Session(engine) as session:
        with pytest.raises(BookNotFound) as exc:
            read_book(session, id=random_uuid)
        assert f"Book with id {random_uuid} not found." in str(exc.value)

def test_read_book_raises_ValueError_when_both_title_and_id_provided():
    with Session(engine) as session:
        with pytest.raises(ValueError) as exc:
            read_book(session, title="a", id=uuid.uuid4())
        assert "Provide title or id, not both." in str(exc.value)


def test_read_book_raises_ValueError_when_no_title_or_id_provided():
    with Session(engine) as session:
        with pytest.raises(ValueError) as exc:
            read_book(session)
        assert "Provide title or id." in str(exc.value)


## Book - Update
def test_update_book_correctly_executes_partial_update_on_existing_book():
    global existing_book_id
    with Session(engine) as session:
        updated_book = update_book(
            session,
            data=BookUpdate(title="book1_updated", visibility_to_others=False),
            title="book1",
        )
        assert updated_book.title == "book1_updated"
        assert updated_book.rating == 5
        assert updated_book.visibility_to_others == False


def test_update_book_raises_BookNotFound_when_book_does_not_exist_for_title_provided():
    with Session(engine) as session:
        with pytest.raises(BookNotFound) as exc:
            update_book(session, data=BookUpdate(title="wont_happen"), title="not_real")
        assert "Book not_real not found." in str(exc.value)

## Book - Delete
def test_delete_book_deletes_book_successfully():
    with Session(engine) as session:
        delete_book(session, title="book1_updated")
        with pytest.raises(BookNotFound):
            read_book(session, title="book1_updated")
