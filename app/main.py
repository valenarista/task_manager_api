from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.api.router import api_router
from app.models.user import User
from app.models.task import Task


app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "API is running"}


