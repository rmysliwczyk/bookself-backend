import uuid

from fastapi import APIRouter
from app.db_operations.dependencies import SessionDep
from app.db_operations.user import create_user, read_all_users, read_user, update_user
from app.models.user import User, UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix="/users")

@router.post("", response_model=UserPublic)
def create(session: SessionDep, data: UserCreate) -> User:
    new_user = create_user(session, data)
    return new_user

@router.get("", response_model=list[UserPublic])
def read_all(session: SessionDep) -> list[User]:
    users = read_all_users(session)
    return users

@router.get("/{user_id}", response_model=UserPublic)
def read(session: SessionDep, user_id: uuid.UUID) -> User:
    user = read_user(session, id=user_id)
    return user

@router.put("/{user_id}", response_model=UserPublic)
def update(session: SessionDep, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = update_user(session, id=user_id, data=data)
    return user
