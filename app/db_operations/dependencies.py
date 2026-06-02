import os

from app.db_operations.user import create_user
from app.models.user import *
from app.models.book import *
from app.settings import Settings

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated

engine = None # Will be initialized in initialize_database on startup

def get_session():
    with Session(engine) as session:
        yield session

def create_admin(session: Session):
    settings = Settings()
    admin_username = settings.admin_username
    admin_password = settings.admin_password
    create_user(session, user=UserCreate(username=admin_username, password=admin_password, role=USER_ROLE.ADMIN))

def initialize_database():
    global engine
    settings = Settings()
    DB_URL = settings.database_url
    engine = create_engine(DB_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            create_admin(session)
        except IntegrityError:
            pass #Initial Admin account already exists.


SessionDep = Annotated[Session, Depends(get_session)]
