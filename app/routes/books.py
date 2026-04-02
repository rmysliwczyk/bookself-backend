from app.db_operations.dependencies import SessionDep
from app.db_operations.book import create_book
from app.models.book import Book, BookCreate, BookPublic

from fastapi.routing import APIRouter

router = APIRouter(prefix="/books")


@router.post("", response_model=BookPublic)
def create(session: SessionDep, data: BookCreate) -> Book:
    new_book = create_book(session, data)
    return new_book
