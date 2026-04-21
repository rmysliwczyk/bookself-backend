import uuid

from app.models.book import Book, BookCreate, BookUpdate
from sqlmodel import Session, select


class BookNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


def create_book(session: Session, book: BookCreate) -> Book:
    book = BookCreate.model_validate(book)
    new_book = Book.model_validate(book)
    session.add(new_book)
    session.commit()
    session.refresh(new_book)
    return new_book


def read_book(session: Session, id: uuid.UUID | None = None) -> Book:
    book = None

    if not id:
        raise ValueError("Provide book id.")

    book = session.exec(select(Book).where(Book.id == id)).first()
    if not book:
        raise BookNotFound(f"Book with id {id} not found.")

    return book

def read_all_books(session: Session) -> list[Book]:
    return list(session.exec(select(Book)).all())

def update_book(
    session: Session,
    data: BookUpdate,
    id: uuid.UUID | None = None,
) -> Book:
    book = read_book(session, id=id)
    BookUpdate.model_validate(book)
    book.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(book)
    session.commit()
    session.refresh(book)

    return book


def delete_book(session: Session, id: uuid.UUID | None = None):
    book_for_deletion = read_book(session, id=id)
    session.delete(book_for_deletion)
    session.commit()
