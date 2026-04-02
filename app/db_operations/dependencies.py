from app.models.user import *
from app.models.book import *

from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated

DB_URL = "sqlite:///database.db"
engine = create_engine(DB_URL)

SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
