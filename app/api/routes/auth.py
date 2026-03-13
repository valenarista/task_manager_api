import logging

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.errors import login_invalid_credentials_error
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

@router.post(
    "/login",
    responses={
        400: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "invalid_credentials",
                            "message": "Invalid email or password",
                        },
                        "detail": "Invalid email or password",
                    }
                }
            },
        },
        422: {
            "description": "Validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "validation_error",
                            "message": "Validation failed",
                            "details": [
                                {
                                    "loc": ["body", "username"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ],
                        },
                        "detail": "Validation failed",
                    }
                }
            },
        },
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed login attempt with email: %s", form_data.username)
        raise login_invalid_credentials_error()

    access_token = create_access_token(data={"sub": user.email})
    logger.info("User logged in successfully with email: %s", user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {
            "description": "Not authenticated or invalid token",
            "content": {
                "application/json": {
                    "examples": {
                        "not_authenticated": {
                            "summary": "Missing token",
                            "value": {
                                "error": {"code": "http_401", "message": "Not authenticated"},
                                "detail": "Not authenticated",
                            },
                        },
                        "invalid_token": {
                            "summary": "Invalid token",
                            "value": {
                                "error": {
                                    "code": "invalid_credentials",
                                    "message": "Could not validate credentials",
                                },
                                "detail": "Could not validate credentials",
                            },
                        },
                    }
                }
            },
        }
    },
)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    logger.info("Fetching user information for email: %s", current_user.email)
    return current_user
