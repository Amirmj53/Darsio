from fastapi import FastAPI,Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles



from .database import Base, engine
from app.routers import documents, pages





app = FastAPI()


app.mount(
    "/static", 
    StaticFiles(directory="static"), 
    name="static"
)

templates = Jinja2Templates(directory="templates")


app.include_router(documents.router)
app.include_router(pages.router)

Base.metadata.create_all(bind=engine)



