import uuid

from app.db_operations.dependencies import SessionDep
from app.db_operations.book import BookNotFound, create_book, delete_book, read_all_books, update_book
from app.db_operations.user import read_user
from app.models.book import Book, BookCreate, BookPublic, BookUpdate
from app.models.user import User, USER_ROLE
from app.util.auth import allowed_roles, get_current_user
from fastapi import Depends, Response, HTTPException
from fastapi.routing import APIRouter
from typing import Annotated

router = APIRouter(prefix="/books")


@router.post("", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER]))])
def create(session: SessionDep, data: BookCreate, current_user: Annotated[User, Depends(get_current_user)]) -> Book:
    if data.user_id != current_user.id and current_user.role != USER_ROLE.ADMIN:
        raise HTTPException(status_code=401, detail="Not authorized")
    new_book = create_book(session, data)
    return new_book

@router.get("", response_model=list[BookPublic], dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN]))])
def read_all(session: SessionDep) -> list[Book]:
    books = read_all_books(session)
    return books

@router.get("/{user_id}", response_model=list[BookPublic], dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER]))])
def read(session: SessionDep, user_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)]) -> list[Book]:
    user = read_user(session, id=user_id)
    books = user.books
    if user_id != current_user.id and current_user.role != USER_ROLE.ADMIN:
        books = [book for book in user.books if book.visibility_to_others == True]
    return books

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
