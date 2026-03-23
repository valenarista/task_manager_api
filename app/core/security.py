import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def create_refresh_token_in_db(db: Session, user_id: int) -> str:
    from app.models.refresh_token import RefreshToken

    token = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    return token


def validate_refresh_token(db: Session, token: str) -> "RefreshToken | None":
    from app.models.refresh_token import RefreshToken

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(UTC),
    ).first()

    return db_token


def revoke_refresh_token(db: Session, token: str) -> bool:
    from app.models.refresh_token import RefreshToken

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked_at.is_(None),
    ).first()

    if db_token:
        db_token.revoked_at = datetime.now(UTC)
        db.commit()
        return True

    return False
