import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    logger.info("Attempting to create user with email: %s", user.email)
    if db.query(User).filter(User.email == user.email).first():
        logger.warning("Email already registered: %s", user.email)
        raise HTTPException(
            status_code=409,
            detail={"code": "email_already_registered", "message": "Email already registered"},
        )
    
    db_user = User(email=user.email, hashed_password=hash_password(user.password))
    db.add(db_user)
    try: 
        db.commit()
    except IntegrityError as err:
        db.rollback()
        logger.warning("Failed to create user with email: %s", user.email)
        raise HTTPException(
            status_code=409,
            detail={"code": "email_already_registered", "message": "Email already registered"},
        ) from err
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while creating user with email: %s", user.email)
        raise
    db.refresh(db_user)
    logger.info("User created successfully with email: %s", db_user.email)
    return db_user
