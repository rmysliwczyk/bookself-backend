from app.util.cryptography import hash_password, verify_password
from pwdlib import PasswordHash


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
