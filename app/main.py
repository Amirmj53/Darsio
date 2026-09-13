from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel 
app = FastAPI()






@app.get("/")
async def root():
    return {"message": "Hello, this is from Darsio"}


class Document(BaseModel):
    title:str
    filename:str
    file_type:str



class DocumentResponse(BaseModel):
    title:str
    filename:str
    file_type:str


@app.post("/document", response_model=DocumentResponse, status_code = status.HTTP_201_CREATED)
async def create_document(document: Document):
    return document