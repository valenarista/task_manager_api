from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.models import user
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User

app = FastAPI()
Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user