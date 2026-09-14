from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.services.documents import format_file_size


router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    documents = db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "documents": documents,
            "format_file_size" : format_file_size
        }
    )