
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.chat import Conversation


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False
    )

    first_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    last_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    display_name:Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    avatar_path:Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    education_level: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    field_of_study: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    activity_field: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    allow_data_usage: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
