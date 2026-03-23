import uuid

from app.models.user import User, UserCreate, UserUpdate
from app.util.cryptography import hash_password
from sqlmodel import col, Session, select


class UserNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


def create_user(session: Session, user: UserCreate) -> User:
    user = UserCreate.model_validate(user)
    hashed_password = hash_password(user.password)

    user_create_fields = user.model_dump()
    del user_create_fields["password"]

    new_user = User(**user_create_fields, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


def read_user(
    session: Session, username: str | None = None, id: uuid.UUID | None = None
) -> User:
    user = None

    if username and id:
        raise ValueError("Provide username or id, not both.")
    elif username:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise UserNotFound(f"User {username} not found.")
    elif id:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise UserNotFound(f"User with id {id} not found.")
    else:
        raise ValueError("Provide username or id.")

    return user


def update_user(
    session: Session,
    data: UserUpdate,
    username: str | None = None,
    id: uuid.UUID | None = None,
) -> User:
    user = read_user(session, username=username, id=id)
    dumped_update_data = data.model_dump(exclude_unset=True)

    following_ids = []
    if "following_ids" in dumped_update_data:
        following_ids = dumped_update_data["following_ids"]
        del dumped_update_data["following_ids"]
    if "password" in dumped_update_data:
        password = dumped_update_data["password"]
        del dumped_update_data["password"]
        dumped_update_data["hashed_password"] = hash_password(password)

    user.sqlmodel_update(dumped_update_data)
    if following_ids:
        if user.id in following_ids:
            raise ValueError("User cannot self-follow.")
        followed_users_in_db = list(
            session.exec(select(User).where(col(User.id).in_(following_ids))).all()
        )
        for followed_user in followed_users_in_db:
            following_ids.remove(followed_user.id)
        if following_ids:
            raise UserNotFound(
                f"Followed users: {" ".join([str(following_id) for following_id in following_ids])} not found."
            )
        else:
            user.following = followed_users_in_db
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def delete_user(
    session: Session, username: str | None = None, id: uuid.UUID | None = None
) -> None:
    user = read_user(session, username=username, id=id)
    session.delete(user)
    session.commit()
