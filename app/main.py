from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    status
)
from pydantic import BaseModel 
from pathlib import Path

from .database import Base, engine, get_db
from sqlalchemy import String, DateTime , select
from sqlalchemy.orm import Mapped, mapped_column, Session
from datetime import datetime
from uuid import uuid4



UPLOAD_DIR = Path("uploads")

app = FastAPI()




#DatabaseClass
class Document(Base):
    __tablename__ = "documents"

    id:Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str] = mapped_column(String(255))
    filename : Mapped[str] = mapped_column(String(255))
    stored_filename : Mapped[str] = mapped_column(String(255), unique=True)
    file_type : Mapped[str] = mapped_column(String(50))
    file_size : Mapped[int] = mapped_column()

    created_at : Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now
    )

Base.metadata.create_all(bind=engine)



@app.get("/")
async def root():
    return {"message": "Hello, this is from Darsio"}


@app.post("/document", status_code = status.HTTP_201_CREATED)
async def create_document(
    title: str = Form(...),
    file : UploadFile =  File(...),
    db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Only PDF fiels are supported"
        )

    stored_filename = f"{uuid4()}.pdf"
    file_path = UPLOAD_DIR / stored_filename

    file_size = 0

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024*1024):
            buffer.write(chunk)
            file_size += len(chunk)
    
    document = Document(
        title = title,
        filename = file.filename,
        file_type = file.content_type,
        stored_filename = stored_filename,
        file_size = file_size,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id" : document.id,
        "title" : document.title,
        "filename" : document.filename,
        "file_type" : document.file_type,
        "file_size" : document.file_size,
        "created_at" : document.created_at,
    }

# Read Files 

@app.get("/documents")
async def get_documents(db: Session = Depends(get_db)):
    documents = db.scalars(
        select(Document).order_by(Document.created_at.desc())
    ).all()

    return documents


@app.get("/documents/{document_id}")
async def get_document(
    document_id: int, 
    db : Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document



