import uuid

from app.db_operations.dependencies import SessionDep
from app.db_operations.book import BookNotFound, create_book, delete_book, read_all_books, update_book
from app.db_operations.user import read_user
from app.models.book import Book, BookCreate, BookPublic, BookUpdate

from fastapi import Response
from fastapi.routing import APIRouter

router = APIRouter(prefix="/books")


@router.post("", response_model=BookPublic)
def create(session: SessionDep, data: BookCreate) -> Book:
    new_book = create_book(session, data)
    return new_book

@router.get("", response_model=list[BookPublic])
def read_all(session: SessionDep) -> list[Book]:
    books = read_all_books(session)
    return books

@router.get("/{user_id}", response_model=list[BookPublic])
def read(session: SessionDep, user_id: uuid.UUID) -> list[Book]:
    user = read_user(session, id=user_id)
    return user.books

@router.patch("/{book_id}", response_model=BookPublic)
def update(session: SessionDep, book_id: uuid.UUID, data: BookUpdate) -> Book:
    book = update_book(session, data, id=book_id)
    return book

@router.delete("/{book_id}")
def delete(session: SessionDep, book_id: uuid.UUID) -> Response:
    try:
        delete_book(session, id=book_id)
        return Response(status_code=200, content="OK")
    except BookNotFound:
        return Response(status_code=404, content="Book not found")
