from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetail,
    ConversationRename,
    MessageCreate,
    MessageResponse,
    MessageUpdate
)
from app.services import chat as chat_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.get_user_conversations(db, current_user)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.create_conversation(db, current_user, data)

@router.get("/conversations/search", response_model=list[ConversationResponse])
def search_conversations(
    q: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.search_conversations(db, current_user, q)


@router.delete(
    "/conversations/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service.delete_conversation(db, current_user, public_id)
    return None

@router.post(
    "/conversations/{public_id}/restore",
    response_model=ConversationResponse
)
def restore_conversation(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.restore_conversation(db, current_user, public_id)


@router.get(
    "/conversations/{public_id}",
    response_model=ConversationDetail
)
def get_conversation(
    public_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.get_conversation(db, current_user, public_id)


@router.patch("/conversations/{public_id}/pin", response_model=ConversationResponse)
async def toggle_pin(
    public_id :str,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db),
):
    return chat_service.toggle_pin_conversation(db, current_user, public_id)

@router.patch("/conversations/{public_id}/rename", response_model=ConversationResponse)
def rename_conversation(
    public_id: str,
    data: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.rename_conversation(db, current_user, public_id, data.title)




@router.patch(
    "/messages/{message_id}",
    response_model=MessageResponse
)
def edit_message(
    message_id: int,
    data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.edit_message(
        db, current_user, message_id, data.content
    )

@router.post(
    "/conversations/{public_id}/messages",
    response_model=MessageResponse
)
def send_message(
    public_id: str,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.send_message(db, current_user, public_id, data)