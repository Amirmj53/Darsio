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


    if user_exists(
        db, user_data.username, str(user_data.email)
    ):
        raise ValueError(
            "Username or email already exists."
        )
    
        
    
    user = User(
        username = user_data.username,
        email = str(user_data.email),
        password_hash = hash_password(
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
            "Username or email already exists."
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

    