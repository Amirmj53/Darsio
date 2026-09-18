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


@router.delete(
        "/conversation/{conversation_id}",
        status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id : int,
    current_user : User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    chat_service.delete_conversation(db, current_user, conversation_id)
    return None



@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.get_conversation(db, current_user, conversation_id)


@router.patch("/conversations/{conversation_id}/pin", response_model=ConversationResponse)
async def toggle_pin(
    conversation_id :int,
    current_user:User = Depends(get_current_user),
    db:Session = Depends(get_db),
):
    return chat_service.toggle_pin_conversation(db, current_user, conversation_id)

@router.patch("/conversations/{conversation_id}/rename", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: int,
    data: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.rename_conversation(db, current_user, conversation_id, data.title)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return chat_service.send_message(db, current_user, conversation_id, data)