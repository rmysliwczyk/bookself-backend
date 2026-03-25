import jwt
import os

from app.util.cryptography import hash_password, verify_password
from app.util.jwt_tokens import jwt_encode
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

ALGORITHM = os.environ["ALGORITHM"]
SECRET_KEY = os.environ["SECRET_KEY"]

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

# JWT tokens functions
def test_jwt_encode_encodes_user_data_correctly():
    common_start_date = datetime.now()
    data = {"username": "test", "password": "pass"}
    data_local = data.copy()
    data_local.update({"exp": (common_start_date + timedelta(minutes=5))}) # type: ignore
    token_compare = jwt.encode(data_local, SECRET_KEY, algorithm=ALGORITHM)
    token = jwt_encode(data, common_start_date, timedelta(minutes=5))
    assert token_compare == token
