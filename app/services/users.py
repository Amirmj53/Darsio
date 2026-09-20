import re
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import ProfileUpdate, PasswordChange
from app.services.auth import hash_password, verify_password

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


def _avatar_url(user: User) -> str | None:
    if not user.avatar_path:
        return None
    return f"/uploads/avatars/{user.avatar_path}"


def serialize_profile(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": _avatar_url(user),
        "is_admin": user.is_admin,
        "created_at": user.created_at,
    }


def get_profile(user: User) -> dict:
    return serialize_profile(user)


def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    if data.username is not None and data.username != user.username:
        exists = db.scalar(
            select(User).where(
                User.username == data.username,
                User.id != user.id,
            )
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="این یوزرنیم قبلاً استفاده شده است",
            )
        user.username = data.username

    if data.display_name is not None:
        user.display_name = data.display_name.strip() or None



    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز عبور فعلی اشتباه است",
        )
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز جدید باید با رمز فعلی متفاوت باشد",
        )
    user.password_hash = hash_password(data.new_password)
    db.commit()


def update_avatar(db: Session, user: User, file: UploadFile) -> User:
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فقط تصویر JPG، PNG یا WEBP مجاز است",
        )

    content = file.file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="حجم تصویر حداکثر ۲ مگابایت باشد",
        )

    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[file.content_type]

    filename = f"user_{user.id}{ext}"
    path = AVATAR_DIR / filename

    # حذف آواتار قبلی با پسوند دیگر
    for old in AVATAR_DIR.glob(f"user_{user.id}.*"):
        if old.name != filename:
            old.unlink(missing_ok=True)

    path.write_bytes(content)
    user.avatar_path = filename
    db.commit()
    db.refresh(user)
    return user


def remove_avatar(db: Session, user: User) -> User:
    if user.avatar_path:
        old = AVATAR_DIR / user.avatar_path
        old.unlink(missing_ok=True)
        user.avatar_path = None
        db.commit()
        db.refresh(user)
    return user