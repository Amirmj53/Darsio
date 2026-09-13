from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel 
from pathlib import Path


UPLOAD_DIR = Path("uploads")

app = FastAPI()









@app.get("/")
async def root():
    return {"message": "Hello, this is from Darsio"}


@app.post("/document", status_code = status.HTTP_201_CREATED)
async def create_document(file : UploadFile =  File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Only PDF fiels are supported"
        )

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024*1024):
            buffer.write(chunk)
    


    return {
        "filename" : file.filename,
        "content_type" : file.content_type,
        "message" : "Document uploaded successfully"
    }