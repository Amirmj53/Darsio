from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware


from .database import Base, engine
from app.routers import documents, pages, auth, chat

from app.models import Document, User
from app.services.auth import hash_password, verify_password


app = FastAPI()


app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_THIS_LATER"
)

app.mount(
    "/static", 
    StaticFiles(directory="static"), 
    name="static"
)



Base.metadata.create_all(bind=engine)




app.include_router(documents.router)
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(chat.router)




