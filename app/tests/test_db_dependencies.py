from app.db_operations.dependencies import get_session
from sqlmodel import Session


def test_get_session_returns_a_session_object():
    session = get_session()
    assert type(session.__next__()) is Session
