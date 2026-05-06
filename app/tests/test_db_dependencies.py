import os
import pytest

from app.db_operations.dependencies import get_session, create_admin
from app.db_operations.user import read_user
from app.main import app
from sqlmodel import create_engine, Session, StaticPool, SQLModel
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(name="session", scope="module")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

def test_get_session_returns_a_session_object():
    session = get_session()
    assert type(session.__next__()) is Session

def test_create_default_admin_creates_a_default_admin(session: Session):
    admin_username = os.getenv("ADMIN_USERNAME")
    assert admin_username != None
    create_admin(session)
    user = read_user(session, username=admin_username)
    assert user.username == admin_username

