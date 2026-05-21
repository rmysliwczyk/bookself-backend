import jwt
import pytest
import os
import types

from app.db_operations.dependencies import get_session
from app.db_operations.user import create_user, delete_user, read_user, UserNotFound
from app.main import app
from app.models.user import *
from app.util.cryptography import hash_password, verify_password
from app.util.auth import jwt_encode, jwt_decode, get_current_user, allowed_roles
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlmodel import create_engine, Session, StaticPool, SQLModel


load_dotenv()

ALGORITHM = os.environ["ALGORITHM"]
SECRET_KEY = os.environ["SECRET_KEY"]

existing_user_id = None
existing_jwt_token = ""

@pytest.fixture(name="session", scope="module")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", scope="module")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="token", scope="module")
def token_fixture(session: Session, client: TestClient):
    try:
        read_user(session, username="fixture-user")
    except UserNotFound:
        create_user(session, UserCreate(username="fixture-user", password="password", role=USER_ROLE.REGULAR_USER))

    post_response = client.post("/users/login", data={"username": "fixture-user", "password": "password"})
    return post_response.json()["access_token"]

# Cryptographic functions
def test_hash_password_hashes_password_correctly():
    password = "test"
    result = hash_password(password)
    pwd_hash = PasswordHash.recommended()
    assert pwd_hash.verify(password, result)


def test_verify_password_verifies_password_correctly():
    password = "test"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password) == True


# Auth functions
def test_jwt_encode_encodes_user_data_correctly(session: Session):
    global existing_jwt_token
    global existing_user_id
    user = create_user(session, UserCreate(username="test", password="password", role=USER_ROLE.ADMIN))
    common_start_date = datetime.now()
    data = {"sub": user.username}
    data_local = data.copy()
    data_local.update({"exp": (common_start_date + timedelta(minutes=5))})  # type: ignore
    token_compare = jwt.encode(data_local, SECRET_KEY, algorithm=ALGORITHM)
    token = jwt_encode(data, common_start_date, timedelta(minutes=5))
    assert token_compare == token
    existing_jwt_token = token
    existing_user_id = user.id

def test_get_current_user_correctly_retrieves_user_from_token(session: Session):
    global existing_jwt_token
    global existing_user_id
    user = get_current_user(existing_jwt_token, session)
    assert user.username == "test"
    assert user.id == existing_user_id

def test_login_returns_token_when_valid_credentials_provided(client: TestClient):
    post_response = client.post("/users/login", data={"username": "test", "password": "password"})
    assert post_response.status_code == 200
    assert post_response.json()["token_type"] == "bearer"
    payload = jwt_decode(post_response.json()["access_token"])
    assert payload["sub"] == "test"

def test_login_returns_401_when_invalid_username_provided(client: TestClient):
    post_response = client.post("/users/login", data={"username": "notindatabase", "password": "password"})
    assert post_response.status_code == 401
    assert post_response.json()["detail"] == "Invalid username or password"

def test_login_returns_401_when_invalid_password_provided(client: TestClient):
    post_response = client.post("/users/login", data={"username": "test", "password": "incorrect_password"})
    assert post_response.status_code == 401
    assert post_response.json()["detail"] == "Invalid username or password"

def test_get_current_user_raises_exception_when_sub_not_in_token(session: Session):
    bad_token = jwt_encode({"not_sub": "something"})
    with pytest.raises(HTTPException):
        get_current_user(bad_token, session)

def test_get_current_user_raises_exception_when_sub_contains_invalid_user(session: Session):
    bad_token = jwt_encode({"sub": "not_real_user"})
    with pytest.raises(HTTPException):
        get_current_user(bad_token, session)

def test_get_current_user_raises_exception_when_jwt_token_invalid(session: Session):
    bad_token = "THISISNOTREALLYAJWTTOKEN"
    with pytest.raises(HTTPException):
        get_current_user(bad_token, session)

def test_allowed_roles_returns_a_function():
    check_roles_func = allowed_roles([USER_ROLE.ADMIN, USER_ROLE.REGULAR_USER])
    assert isinstance(check_roles_func, types.FunctionType)

def test_read_all_users_returns_401_for_regular_user(client: TestClient, token: str):
    get_response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 401
    assert get_response.json()["detail"] == "Not authorized"

def test_read_user_user_id_returns_401_for_regular_user(client: TestClient, token: str):
    global existing_user_id
    post_response = client.get(f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"})
    assert post_response.status_code == 401
    assert post_response.json()["detail"] == "Not authorized"

def test_update_users_user_id_returns_401_for_regular_user(client: TestClient, token: str):
    global existing_user_id
    patch_response = client.patch(f"/users/{existing_user_id}", headers={"Authorization": f"Bearer {token}"}, json={"username": "test-new-1"})
    assert patch_response.status_code == 401
    assert patch_response.json()["detail"] == "Not authorized"


