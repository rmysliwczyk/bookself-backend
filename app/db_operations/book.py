import uuid

from app.models.book import Book, BookCreate, BookUpdate
from app.util.cryptography import hash_password
from sqlmodel import col, Session, select


class BookNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


def create_book(session: Session, book: BookCreate) -> Book:
    book = BookCreate.model_validate(book)
    new_book = Book(**book.model_dump())
    session.add(new_book)
    session.commit()
    session.refresh(new_book)
    return new_book


def read_book(
    session: Session, id: uuid.UUID | None = None
) -> Book:
    book = None

    if not id:
        raise ValueError("Provide book id.")
    
    book = session.exec(select(Book).where(Book.id == id)).first()
    if not book:
        raise BookNotFound(f"Book with id {id} not found.")
    
    return book


def update_book(
    session: Session,
    data: BookUpdate,
    id: uuid.UUID | None = None,
) -> Book:
    book = read_book(session, id=id)

    book.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(book)
    session.commit()
    session.refresh(book)

    return book

def delete_book(session: Session, id: uuid.UUID | None = None):
    book_for_deletion = read_book(session, id=id)
    session.delete(book_for_deletion)
    session.commit()

