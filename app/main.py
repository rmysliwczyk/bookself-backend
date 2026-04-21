from app.routes.books import router as books_router
from app.routes.users import router as users_router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])


@app.get("/status", status_code=200)
def read_status():
    pass


app.include_router(books_router)
app.include_router(users_router)
