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
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, Session

UPLOAD_DIR = Path("uploads")

app = FastAPI()




#DatabaseClass
class Document(Base):
    __tablename__ = "documents"

    id:Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str] = mapped_column(String(255))
    filename : Mapped[str] = mapped_column(String(255))
    file_type : Mapped[str] = mapped_column(String(50))

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

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024*1024):
            buffer.write(chunk)
    
    document = Document(
        title = title,
        filename = file.filename,
        file_type = file.content_type

    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id" : document.id,
        "title" : document.title,
        "filename" : document.filename,
        "file_type" : document.file_type
    }
