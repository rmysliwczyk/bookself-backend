import uuid

from pydantic import AnyUrl, ConfigDict
from pydantic_extra_types.isbn import ISBN
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

MAX_TITLE_LENGTH = 256
MAX_REVIEW_LENGTH = 10192


class BaseBook(SQLModel):
    model_config = ConfigDict(extra="forbid")  # type: ignore
    title: str = Field(max_length=MAX_TITLE_LENGTH)
    rating: int = Field(ge=1, le=10)
    visibility_to_others: bool = Field()
    review: str | None = Field(max_length=MAX_REVIEW_LENGTH, default=None)


class Book(BaseBook, table=True):
    id: uuid.UUID | None = Field(primary_key=True, default_factory=uuid.uuid4)
    cover_photo_url: str | None = Field(default=None)
    isbn: str | None = Field(default=None)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="books")


class BookCreate(BaseBook):
    cover_photo_url: AnyUrl | None = Field(default=None)
    isbn: ISBN | None = Field(default=None)
    user_id: uuid.UUID = Field()


class BookPublic(BaseBook):
    id: uuid.UUID
    user_id: uuid.UUID


class BookUpdate(SQLModel):
    title: str | None = Field(max_length=MAX_TITLE_LENGTH, default=None)
    rating: int | None = Field(ge=1, le=10, default=None)
    visibility_to_others: bool | None = None
    review: str | None = Field(max_length=MAX_REVIEW_LENGTH, default=None)
    cover_photo_url: AnyUrl | None = None
    isbn: ISBN | None = None
    user_id: uuid.UUID | None = None
