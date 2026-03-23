import uuid

from enum import Enum
from pydantic import ConfigDict
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.book import Book, BookPublic

class UserFollowerLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    follower_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )


class USER_ROLE(Enum):
    ADMIN = "ADMIN"
    REGULAR_USER = "REGULAR_USER"


class BaseUser(SQLModel):
    model_config = ConfigDict(extra="forbid")  # type: ignore
    username: str = Field(unique=True)
    role: USER_ROLE = Field()


class User(BaseUser, table=True):
    id: uuid.UUID | None = Field(primary_key=True, default_factory=uuid.uuid4)
    hashed_password: str = Field()
    books: list['Book'] = Relationship(back_populates="user", cascade_delete=True)
    following: list['User'] = Relationship(
        back_populates="followers",
        link_model=UserFollowerLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowerLink.follower_id",
            "secondaryjoin": "User.id==UserFollowerLink.user_id",
        },
    )
    followers: list['User'] = Relationship(
        back_populates="following",
        link_model=UserFollowerLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowerLink.user_id",
            "secondaryjoin": "User.id==UserFollowerLink.follower_id",
        },
    )


class UserCreate(BaseUser):
    password: str


class UserPublic(BaseUser):
    id: uuid.UUID
    books: list['BookPublic'] | None = None


class UserPublicWithFollowers(BaseUser):
    id: uuid.UUID
    following: list[UserPublic] | None = None
    followers: list[UserPublic] | None = None


class UserUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")  # type: ignore
    username: str | None = None
    password: str | None = None
    role: USER_ROLE | None = None
    following_ids: list[uuid.UUID | None] | None = None
