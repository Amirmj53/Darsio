from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.document import Document

MAX_SUPERADMINS = 3


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)


def get_stats(db: Session) -> dict:
    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    users_active = db.scalar(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    ) or 0
    users_today = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.created_at >= _start_of_today_utc())
    ) or 0

    conversations_total = db.scalar(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.deleted_at.is_(None))
    ) or 0

    messages_total = db.scalar(select(func.count()).select_from(Message)) or 0
    documents_total = db.scalar(select(func.count()).select_from(Document)) or 0

    return {
        "users_total": users_total,
        "users_today": users_today,
        "users_active": users_active,
        "conversations_total": conversations_total,
        "messages_total": messages_total,
        "documents_total": documents_total,
    }


def list_users(
    db: Session,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.display_name.ilike(like),
            )
        )
    return list(db.scalars(stmt.offset(skip).limit(min(limit, 100))).all())


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    return user


def update_user(
    db: Session,
    actor: User,
    user_id: int,
    is_active: bool | None = None,
    is_admin: bool | None = None,
) -> User:
    target = get_user(db, user_id)


    if target.is_superadmin and not actor.is_superadmin:
        raise HTTPException(
            status_code=403,
            detail="امکان تغییر سوپرادمین وجود ندارد",
        )

    # کسی خودش را غیرفعال/تنزیل نکند از این مسیر (ساده‌سازی امن)
    if target.id == actor.id:
        raise HTTPException(
            status_code=400,
            detail="نمی‌توانید وضعیت خودتان را از اینجا تغییر دهید",
        )

    if is_active is not None:
        target.is_active = is_active

    if is_admin is not None:
        if not actor.is_superadmin:
            raise HTTPException(
                status_code=403,
                detail="فقط سوپرادمین می‌تواند نقش ادمین را تغییر دهد",
            )
        if target.is_superadmin:
            raise HTTPException(
                status_code=400,
                detail="نقش سوپرادمین از این مسیر تغییر نمی‌کند",
            )
        target.is_admin = is_admin

    db.commit()
    db.refresh(target)
    return target


def list_conversations(
    db: Session,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    stmt = (
        select(Conversation, User.username)
        .join(User, User.id == Conversation.user_id)
        .where(Conversation.deleted_at.is_(None))
        .order_by(Conversation.updated_at.desc())
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Conversation.title.ilike(like), User.username.ilike(like))
        )

    rows = db.execute(stmt.offset(skip).limit(min(limit, 100))).all()
    result = []
    for conv, username in rows:
        count = db.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conv.id)
        ) or 0
        result.append(
            {
                "id": conv.id,
                "public_id": getattr(conv, "public_id", None),
                "title": conv.title,
                "user_id": conv.user_id,
                "username": username,
                "is_pinned": conv.is_pinned,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": count,
            }
        )
    return result


def get_conversation_detail(db: Session, conversation_id: int) -> dict:
    row = db.execute(
        select(Conversation, User.username)
        .join(User, User.id == Conversation.user_id)
        .where(Conversation.id == conversation_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="مکالمه پیدا نشد")

    conv, username = row
    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        ).all()
    )
    return {
        "id": conv.id,
        "public_id": getattr(conv, "public_id", None),
        "title": conv.title,
        "user_id": conv.user_id,
        "username": username,
        "is_pinned": conv.is_pinned,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "message_count": len(messages),
        "messages": messages,
    }


def delete_conversation_admin(db: Session, conversation_id: int) -> None:
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="مکالمه پیدا نشد")
    conv.deleted_at = datetime.now(timezone.utc)
    db.commit()


def list_documents(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    rows = db.execute(
        select(Document, User.username)
        .join(User, User.id == Document.user_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(min(limit, 100))
    ).all()
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "user_id": doc.user_id,
            "username": username,
            "created_at": doc.created_at,
        }
        for doc, username in rows
    ]


def delete_document_admin(db: Session, document_id: int) -> None:
    from pathlib import Path

    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="فایل پیدا نشد")

    path = Path("uploads") / doc.stored_filename
    if path.exists():
        path.unlink()

    db.delete(doc)
    db.commit()