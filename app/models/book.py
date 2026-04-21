import uuid

from pydantic import HttpUrl, ConfigDict
from pydantic_extra_types.isbn import ISBN
from sqlmodel import Field, Relationship, SQLModel, AutoString, TypeDecorator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

MAX_TITLE_LENGTH = 256
MAX_REVIEW_LENGTH = 10192
MAX_AUTHOR_LENGTH = 256

class HttpUrlType(TypeDecorator):
    impl = AutoString
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value != None:
            return str(value) # pragma: no cover

    def process_result_value(self, value, dialect):
        if value != None:
            return HttpUrl(value) # pragma: no cover


class BaseBook(SQLModel):
    model_config = ConfigDict(extra="forbid")  # type: ignore
    title: str = Field(max_length=MAX_TITLE_LENGTH)
    author: str | None = Field(max_length=MAX_AUTHOR_LENGTH, default=None)
    rating: int = Field(ge=1, le=10)
    visibility_to_others: bool = Field()
    review: str | None = Field(max_length=MAX_REVIEW_LENGTH, default=None)
    cover_photo_url: HttpUrl | None = Field(default=None, sa_type=HttpUrlType)


class Book(BaseBook, table=True):
    id: uuid.UUID | None = Field(primary_key=True, default_factory=uuid.uuid4)
    isbn: str | None = Field(default=None)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="books")


class BookCreate(BaseBook):
    isbn: ISBN | None = Field(default=None)
    user_id: uuid.UUID = Field()


class BookPublic(BaseBook):
    id: uuid.UUID
    user_id: uuid.UUID


class BookUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid") # type: ignore
    title: str | None = Field(max_length=MAX_TITLE_LENGTH, default=None)
    author: str | None = Field(max_length=MAX_AUTHOR_LENGTH, default=None)
    rating: int | None = Field(ge=1, le=10, default=None)
    visibility_to_others: bool | None = None
    review: str | None = Field(max_length=MAX_REVIEW_LENGTH, default=None)
    cover_photo_url: HttpUrl | None = None
    isbn: ISBN | None = None
    user_id: uuid.UUID | None = None
