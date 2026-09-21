"""
Usage:
  python -m scripts.create_superuser
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, engine, Base, ensure_user_columns
from app.models.user import User
from app.services.auth import hash_password
from sqlalchemy import select, func

Base.metadata.create_all(bind=engine)
ensure_user_columns()

MAX_SUPERADMINS = 3


def main() -> None:
    email = input("Email: ").strip().lower()
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count()).select_from(User).where(User.is_superadmin.is_(True))
        ) or 0
        if count >= MAX_SUPERADMINS:
            print(f"حداکثر {MAX_SUPERADMINS} سوپرادمین مجاز است.")
            return

        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            existing.is_admin = True
            existing.is_superadmin = True
            existing.is_active = True
            if password:
                existing.password_hash = hash_password(password)
            db.commit()
            print(f"کاربر موجود به سوپرادمین ارتقا یافت: {email}")
            return

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            is_admin=True,
            is_superadmin=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"سوپرادمین ساخته شد: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()