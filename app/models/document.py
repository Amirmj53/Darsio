from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255)
    )

    filename: Mapped[str] = mapped_column(
        String(255)
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True
    )

    file_type: Mapped[str] = mapped_column(
        String(50)
    )

    file_size: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )