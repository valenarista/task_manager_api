from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.core.auth import get_current_user
from app.schemas.user import UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password): # type: ignore
        logger.warning("Failed login attempt with email: %s", form_data.username)
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user.email})
    logger.info("User logged in successfully with email: %s", user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    logger.info("Fetching user information for email: %s", current_user.email)
    return current_user