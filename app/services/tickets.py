import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketReply
from app.models.user import User


TICKET_DIR = Path("uploads/tickets")
TICKET_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5MB

CATEGORIES = {"general_report", "bug_report"}
STATUSES = {"open", "answered", "closed"}


def _attachment_url(stored_name: str | None) -> str | None:
    if not stored_name:
        return None
    return f"/uploads/tickets/{stored_name}"


def _reply_dict(reply: TicketReply) -> dict:
    return {
        "id": reply.id,
        "author_id": reply.author_id,
        "author_role": reply.author_role,
        "content": reply.content,
        "created_at": reply.created_at,
    }


def _ticket_dict(ticket: Ticket, with_user: bool = False) -> dict:
    data = {
        "id": ticket.id,
        "category": ticket.category,
        "description": ticket.description,
        "status": ticket.status,
        "attachment_url": _attachment_url(ticket.attachment_path),
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "reply_count": len(ticket.replies),
    }
    if with_user:
        data["username"] = ticket.user.username if ticket.user else None
        data["email"] = ticket.user.email if ticket.user else None
    return data


def _ticket_detail_dict(ticket: Ticket, with_user: bool = False) -> dict:
    data = _ticket_dict(ticket, with_user=with_user)
    data["replies"] = [_reply_dict(r) for r in ticket.replies]
    return data


def _validate_category(category: str) -> str:
    category = (category or "").strip()
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="دسته‌بندی تیکت معتبر نیست",
        )
    return category


def _validate_status(value: str) -> str:
    value = (value or "").strip()
    if value not in STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="وضعیت تیکت معتبر نیست",
        )
    return value


async def _save_attachment(file: UploadFile | None) -> str | None:
    if file is None:
        return None

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فقط تصویر JPG، PNG یا WEBP مجاز است",
        )

    content = await file.read()
    if len(content) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حجم تصویر باید حداکثر ۵ مگابایت باشد",
        )

    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[content_type]

    stored_name = f"{uuid.uuid4().hex}{ext}"
    (TICKET_DIR / stored_name).write_bytes(content)
    return stored_name


# ---------------------------------------------------------------------------
# User endpoints
# ---------------------------------------------------------------------------

async def create_ticket(
    db: Session,
    user: User,
    category: str,
    description: str,
    file: UploadFile | None,
) -> Ticket:
    category = _validate_category(category)
    description = (description or "").strip()
    if not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توضیحات تیکت الزامی است",
        )

    stored_name = await _save_attachment(file)

    ticket = Ticket(
        user_id=user.id,
        category=category,
        description=description,
        status="open",
        attachment_path=stored_name,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_user_tickets(db: Session, user: User) -> list[Ticket]:
    return list(
        db.scalars(
            select(Ticket)
            .where(Ticket.user_id == user.id)
            .order_by(Ticket.created_at.desc())
        ).all()
    )


def get_user_ticket(db: Session, user: User, ticket_id: int) -> Ticket:
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.user_id == user.id,
        )
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="تیکت پیدا نشد")
    return ticket


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

def list_admin_tickets(
    db: Session,
    ticket_status: str | None = None,
    category: str | None = None,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Ticket]:
    stmt = (
        select(Ticket)
        .join(User, User.id == Ticket.user_id)
        .order_by(Ticket.created_at.desc())
    )
    if ticket_status:
        stmt = stmt.where(Ticket.status == _validate_status(ticket_status))
    if category:
        stmt = stmt.where(Ticket.category == _validate_category(category))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Ticket.description.ilike(like),
                User.username.ilike(like),
                User.email.ilike(like),
            )
        )
    return list(db.scalars(stmt.offset(skip).limit(min(limit, 100))).all())


def get_admin_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="تیکت پیدا نشد")
    return ticket


def admin_reply(db: Session, actor: User, ticket_id: int, content: str) -> TicketReply:
    ticket = get_admin_ticket(db, ticket_id)
    content = (content or "").strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="متن پاسخ خالی است",
        )

    reply = TicketReply(
        ticket_id=ticket.id,
        author_id=actor.id,
        author_role="admin",
        content=content,
    )
    db.add(reply)

    # auto-mark answered when currently open
    if ticket.status == "open":
        ticket.status = "answered"
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(reply)
    return reply


def admin_update_status(db: Session, ticket_id: int, ticket_status: str) -> Ticket:
    ticket = get_admin_ticket(db, ticket_id)
    ticket.status = _validate_status(ticket_status)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket
