import uuid

from fastapi import APIRouter, Response, HTTPException
from app.db_operations.dependencies import SessionDep
from app.db_operations.user import create_user, delete_user, read_all_users, read_user, update_user, UserNotFound
from app.models.user import User, UserCreate, UserPublic, UserPublicWithFollowers, UserUpdate

router = APIRouter(prefix="/users")

@router.post("", response_model=UserPublic)
def create(session: SessionDep, data: UserCreate) -> User:
    new_user = create_user(session, data)
    return new_user

@router.get("", response_model=list[UserPublicWithFollowers])
def read_all(session: SessionDep) -> list[User]:
    users = read_all_users(session)
    return users

@router.get("/{user_id}", response_model=UserPublicWithFollowers)
def read(session: SessionDep, user_id: uuid.UUID) -> User:
    try:
        user = read_user(session, id=user_id)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserPublicWithFollowers)
def update(session: SessionDep, user_id: uuid.UUID, data: UserUpdate) -> User:
    try:
        user = update_user(session, id=user_id, data=data)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.delete("/{user_id}")
def delete(session: SessionDep, user_id: uuid.UUID) -> Response:
    delete_user(session, id=user_id)
    return Response(status_code=200, content="OK")

