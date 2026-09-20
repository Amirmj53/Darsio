from fastapi import Request
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from datetime import datetime,timezone

from app.models.user import User
from app.schemas.user import UserCreate
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def user_exists(
    db:Session,
    username:str,
    email : str
) -> bool:
    user = db.scalar(
        select(User).where(
            or_(
                User.username == username,
                User.email == email
            )
        )
    )
    return user is not None



def hash_password(password : str) -> str :
    return password_hash.hash(password)

def verify_password(
        password: str,
        hashed_password : str
) -> bool :
    return password_hash.verify(
        password, 
        hashed_password
    )



def get_user_by_email(
    db : Session,
    email: str
) -> User | None:
    return db.scalar(
        select(User).where(
            User.email == email
        )
    )


def get_user_by_username(
        db:Session,
        username : str
) -> User | None:
    return db.scalar(
        select(User).where(
            User.username == username
        )
    )


def create_user(
        db:Session,
        user_data : UserCreate
):
    username = user_data.username
    email = str(user_data.email)

    if get_user_by_email(db, email) is not None:
        raise ValueError("این ایمیل قبلاً ثبت شده است.")

    if get_user_by_username(db, username) is not None:
        raise ValueError("این یوزرنیم قبلاً گرفته شده است.")

    first_name = user_data.first_name.strip()
    last_name = user_data.last_name.strip()

    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        display_name=f"{first_name} {last_name}".strip(),
        education_level=user_data.education_level,
        field_of_study=user_data.field_of_study,
        activity_field=user_data.activity_field,
        allow_data_usage=user_data.allow_data_usage,
        password_hash=hash_password(
            user_data.password
        )
    )

    try: 
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    except IntegrityError:
        db.rollback()

        raise ValueError(
            "ایمیل یا یوزرنیم قبلاً استفاده شده است."
        )



def authenticate_user(
        db:Session,
        email:str,
        password:str
) -> User | None:
    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password, 
        user.password_hash
    ):
        return None

    return user

def login_user(
        request: Request,
        user:User
) -> None:
    request.session.clear()

    request.session["user_id"] = user.id

    user.last_login_at = datetime.now(
        timezone.utc
    )


def logout_user(
    request:Request
) -> None:
    request.session.clear()

    