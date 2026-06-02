import os
import pytest

from app.db_operations.dependencies import create_admin, initialize_database, get_session
from app.db_operations.user import read_user
from app.settings import Settings
from app.main import app, mylifespan

from fastapi.testclient import TestClient
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
    settings = Settings()
    admin_username = settings.admin_username
    assert admin_username != None
    create_admin(session)
    user = read_user(session, username=admin_username)
    assert user.username == admin_username

def test_initialize_database_successfully_initializes_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    initialize_database()
    assert os.path.exists("test.db")
    os.remove("test.db")

def test_initialize_database_skips_initialization_when_db_exists(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    initialize_database()
    assert os.path.exists("test.db")
    initialize_database()
    assert os.path.exists("test.db")
    os.remove("test.db")

def test_fastapi_lifespan_initializes_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    with TestClient(app) as client:
        assert os.path.exists("test.db")
    os.remove("test.db")
