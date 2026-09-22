import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, ensure_user_columns, ensure_conversation_public_ids
from app.routers import documents, pages, auth, chat, users, admin, tickets

from app.models import Document, User
from app.services.auth import hash_password, verify_password
from app.validation import first_friendly_error


app = FastAPI()


SECRET_KEY = os.environ.get("DARSIO_SECRET_KEY", "CHANGE_THIS_LATER")
if SECRET_KEY == "CHANGE_THIS_LATER":
    logging.warning("DARSIO_SECRET_KEY is not set; using insecure default session secret.")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a clean, user-facing message instead of raw Pydantic output."""
    return JSONResponse(
        status_code=422,
        content={"detail": first_friendly_error(exc.errors())},
    )


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


Path("uploads/avatars").mkdir(parents=True, exist_ok=True)
Path("uploads/tickets").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


Base.metadata.create_all(bind=engine)
ensure_user_columns()
ensure_conversation_public_ids()


app.include_router(documents.router)
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(tickets.router)
