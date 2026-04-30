import jwt
import os

from app.db_operations.dependencies import SessionDep
from app.db_operations.user import read_user, UserNotFound
from app.models.user import *
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

load_dotenv()

ALGORITHM = os.environ["ALGORITHM"]
SECRET_KEY = os.environ["SECRET_KEY"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def jwt_encode(data: dict, current_time: datetime = datetime.now(), exp_delta: timedelta = timedelta(minutes=60)):
    data.update({"exp": current_time + exp_delta})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def jwt_decode(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True, "require": ["exp"]})

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Included token is invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt_decode(token)
        if not "sub" in payload:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    try:
        user = read_user(session, username=payload["sub"])
    except UserNotFound:
        raise credentials_exception

    return user


