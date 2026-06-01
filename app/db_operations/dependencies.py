import os

from app.models.user import *
from app.models.book import *
from app.db_operations.user import create_user

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated

load_dotenv()

engine = None # Will be initialized in initialize_database on startup

def get_session():
    with Session(engine) as session:
        yield session

def create_admin(session: Session):
    admin_username = os.environ["ADMIN_USERNAME"]
    admin_password = os.environ["ADMIN_PASSWORD"]
    create_user(session, user=UserCreate(username=admin_username, password=admin_password, role=USER_ROLE.ADMIN))

def initialize_database():
    global engine
    DB_URL = os.environ["DATABASE_URL"]
    engine = create_engine(DB_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            create_admin(session)
        except IntegrityError:
            pass #Initial Admin account already exists.


SessionDep = Annotated[Session, Depends(get_session)]
