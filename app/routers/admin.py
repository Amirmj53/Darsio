from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_superadmin
from app.models.user import User
from app.schemas.admin import (
    AdminStats,
    AdminUserListItem,
    AdminUserUpdate,
    AdminConversationItem,
    AdminConversationDetail,
    AdminDocumentItem,
)
from app.services import admin as admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
def stats(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_stats(db)


@router.get("/users", response_model=list[AdminUserListItem])
def users(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_users(db, q=q, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=AdminUserListItem)
def user_detail(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_user(db, user_id)


@router.patch("/users/{user_id}", response_model=AdminUserListItem)
def user_update(
    user_id: int,
    data: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.update_user(
        db,
        actor=current_admin,
        user_id=user_id,
        is_active=data.is_active,
        is_admin=data.is_admin,
    )


@router.get("/conversations", response_model=list[AdminConversationItem])
def conversations(
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_conversations(db, q=q, skip=skip, limit=limit)


@router.get("/conversations/{conversation_id}", response_model=AdminConversationDetail)
def conversation_detail(
    conversation_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.get_conversation_detail(db, conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def conversation_delete(
    conversation_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    admin_service.delete_conversation_admin(db, conversation_id)
    return None


@router.get("/documents", response_model=list[AdminDocumentItem])
def documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_documents(db, skip=skip, limit=limit)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def document_delete(
    document_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    admin_service.delete_document_admin(db, document_id)
    return None