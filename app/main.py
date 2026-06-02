from app.db_operations.dependencies import *

from app.models.book import *
from app.models.user import *

from app.routes.books import router as books_router
from app.routes.users import router as users_router

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.oauth2 import OAuth2PasswordBearer


@asynccontextmanager
async def mylifespan(app: FastAPI):
    initialize_database()
    yield

app = FastAPI(lifespan=mylifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rebuilding models with incomplete relationships
Book.model_rebuild()
User.model_rebuild()
UserPublic.model_rebuild()
UserPublicWithFollowers.model_rebuild()


@app.get("/status", status_code=200, tags=["Status"])
def read_status():
    return "OK"


app.include_router(books_router, tags=["Books"])
app.include_router(users_router, tags=["Users"])
