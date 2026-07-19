import json
import uuid

from app.db_operations.dependencies import SessionDep
from app.db_operations.book import BookNotFound, create_book, delete_book, read_all_books, update_book
from app.db_operations.user import read_user
from app.models.book import Book, BookCreate, BookPublic, BookUpdate
from app.models.user import User, USER_ROLE
from app.settings import Settings
from app.util.auth import allowed_roles, get_current_user
from fastapi import Depends, Response, Form, UploadFile, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from pydantic import ValidationError
from typing import Annotated

def parse_create_book_data(data: str = Form()) -> BookCreate:
    parsed_json = json.loads(data)
    try:
        return_value = BookCreate.model_validate(parsed_json)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    return return_value

settings = Settings()

router = APIRouter(prefix="/books")
@router.post("", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER]))])
def create(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)], cover_picture: UploadFile, data: Annotated[BookCreate, Depends(parse_create_book_data)]) -> Book:
    if data.user_id != current_user.id and current_user.role != USER_ROLE.ADMIN:
        raise HTTPException(status_code=401, detail="Not authorized")

    extension = ".err"
    match(cover_picture.content_type):
        case "image/jpeg":
            extension = ".jpg"
        case "image/png":
            extension = ".png"
        case _:
            raise RequestValidationError("Invalid image format")

    filepath = f"{settings.media_base_url}{cover_picture.filename if cover_picture.filename else 'unkown'}_{str(data.user_id)}{extension}"
    with open(filepath, "wb") as f:
        f.write(cover_picture.file.read())
    file_url = f"{settings.api_url}{filepath}"
    new_book = create_book(session, data, cover_photo_url=file_url)
    return new_book

@router.get("", response_model=list[BookPublic], dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN]))])
def read_all(session: SessionDep) -> list[Book]:
    books = read_all_books(session)
    return books

@router.patch("/{book_id}", response_model=BookPublic, dependencies=[Depends(allowed_roles([USER_ROLE.ADMIN,USER_ROLE.REGULAR_USER]))])
def update(session: SessionDep, current_user: Annotated[User, Depends(get_current_user)], book_id: uuid.UUID, data: BookUpdate) -> Book:
    if ("user_id" in data.model_dump()):
        new_user_id = data.model_dump()["user_id"]
        if new_user_id != None and new_user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Cannot assign books to other users")
    book = update_book(session, data, id=book_id)
    return book

@router.delete("/{book_id}")
def delete(session: SessionDep, book_id: uuid.UUID) -> Response:
    try:
        delete_book(session, id=book_id)
        return Response(status_code=200, content="OK")
    except BookNotFound:
        return Response(status_code=404, content="Book not found")

@router.get(f"/{settings.media_base_url}")
def get_cover_picture(filename: str) -> FileResponse:
    return FileResponse(path=f"{settings.media_base_url}{filename}", media_type="image/jpeg", filename=filename)
