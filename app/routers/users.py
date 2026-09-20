from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    ProfileResponse,
    ProfileUpdate,
    PasswordChange
)

from app.services import users as users_service


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/me", response_model=ProfileResponse)
def read_my_profile(current_user : User = Depends(get_current_user)):
    return users_service.get_profile(current_user)

@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = users_service.update_profile(db, current_user, data)
    return users_service.serialize_profile(user)



@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    users_service.change_password(db, current_user, data)
    return None


@router.post("/me/avatar", response_model=ProfileResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = users_service.update_avatar(db, current_user, file)
    return users_service.serialize_profile(user)


@router.delete("/me/avatar", response_model=ProfileResponse)
def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = users_service.remove_avatar(db, current_user)
    return users_service.serialize_profile(user)


