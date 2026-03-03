from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")