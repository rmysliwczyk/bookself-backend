import uuid

from app.db_operations.dependencies import SessionDep
from app.db_operations.user import create_user, delete_user, read_all_users, read_user, update_user, UserNotFound
from app.models.user import User, UserCreate, UserPublic, UserPublicWithFollowers, UserUpdate
from app.util.auth import jwt_encode
from app.util.cryptography import verify_password
from fastapi import APIRouter, Form, Response, HTTPException
from typing import Annotated

router = APIRouter(prefix="/users")

@router.post("/login")
def login(session: SessionDep, username: Annotated[str, Form()], password: Annotated[str, Form()]):
    credentials_exception = HTTPException(status_code=401, detail="Invalid username or password")
    try:
        user = read_user(session, username=username)
    except UserNotFound:
        raise credentials_exception

    if not verify_password(password, user.hashed_password):
        raise credentials_exception

    token = jwt_encode({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

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

