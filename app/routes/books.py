import json
import uuid

from app.db_operations.dependencies import SessionDep
from app.db_operations.book import BookNotFound, create_book, delete_book, read_all_books, read_book, update_book
from app.db_operations.user import read_user, UserNotFound
from app.models.book import Book, BookCreate, BookPublic, BookUpdate
from app.models.user import User, USER_ROLE
from app.settings import Settings
from app.util.auth import allowed_roles, get_current_user
from fastapi import Depends, Response, Form, UploadFile, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from PIL import Image
from pydantic import ValidationError
from typing import Annotated

settings = Settings()

router = APIRouter(prefix="/books")
@router.post("", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER]))])
def create(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)], data: BookCreate) -> Book:
    if data.user_id != current_user.id and current_user.role != USER_ROLE.ADMIN:
        raise HTTPException(status_code=401, detail="Not authorized")

    if current_user.role == USER_ROLE.ADMIN:
        try:
            read_user(session, id=data.user_id)
        except UserNotFound:
            raise HTTPException(status_code=404, detail="User not found.")

    new_book = create_book(session, data)
    return new_book

@router.get("", response_model=list[BookPublic], dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN]))])
def read_all(session: SessionDep) -> list[Book]:
    books = read_all_books(session)
    return books

@router.get("/{book_id}", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER]))])
def read_one(session: SessionDep, book_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)]) -> Book:
    try:
        book = read_book(session, id=book_id)
        if book.user_id != current_user.id and current_user.role != USER_ROLE.ADMIN and book.visibility_to_others == False:
            raise BookNotFound("Book can't be shown")
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found")

    return book

@router.patch("/{book_id}", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN,USER_ROLE.REGULAR_USER]))])
def update(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)], book_id: uuid.UUID, data: BookUpdate) -> Book:
    book = read_book(session, id=book_id)

    if data.model_dump()['user_id'] and book.user_id != data.model_dump()['user_id']:
        raise HTTPException(status_code=400, detail="Cannot assign books to other users")

    book = update_book(session, data, id=book_id)
    return book

@router.delete("/{book_id}", dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN,USER_ROLE.REGULAR_USER]))])
def delete(session: SessionDep, current_user: Annotated[User,Depends(get_current_user)], book_id: uuid.UUID) -> Response:
    if current_user.role != USER_ROLE.ADMIN:
        try:
            book = read_book(session, book_id)
        except BookNotFound:
            return Response(status_code=404, content="Book not found")
        if book.user_id != current_user.id:
            raise HTTPException(status_code=401, detail="Can't delete other user's books")

    delete_book(session, id=book_id)
    return Response(status_code=200, content="OK")

@router.put("/{book_id}/cover", dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN,USER_ROLE.REGULAR_USER]))])
def create_cover(session: SessionDep, book_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)], cover_image_file: UploadFile) -> FileResponse:
    settings = Settings()

    try:
        book = read_book(session, id=book_id)
        if book.user_id != current_user.id and current_user.role != USER_ROLE.ADMIN and book.visibility_to_others == False:
            raise BookNotFound("Book can't be shown")
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found")

    if (cover_image_file.content_type not in ["image/jpeg", "image/png"]):
        raise RequestValidationError("Invalid image format")

    filename = f"{str(book_id)}.jpg"
    filepath = f"{settings.media_base_url}{filename}"
    with Image.open(cover_image_file.file) as im:
        im = im.convert("RGB")
        im.save(filepath, format = "JPEG")

    book_data = book.model_dump(exclude={"id"})
    book_data["cover_photo_url"] = f"{settings.api_url}books/{book_id}/cover"
    book = update_book(session, BookUpdate.model_validate(book_data), id=book_id)
    return FileResponse(path=filepath, media_type=cover_image_file.content_type, filename=filename)

@router.get("/{book_id}/cover")
def get_cover_picture(book_id: uuid.UUID) -> FileResponse:
    return FileResponse(path=f"{settings.media_base_url}{book_id}.jpg", media_type="image/jpeg", filename=f'{book_id}.jpg')
