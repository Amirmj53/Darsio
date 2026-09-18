from datetime import datetime, timezone
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.chat import Conversation, Message
from app.models.user import User
from app.schemas.chat import ConversationCreate, MessageCreate



def get_user_conversations(db:Session, user:User) -> list[Conversation]:
    return(
        db.query(Conversation)
        .filter( Conversation.user_id == user.id )
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def create_conversation(
        db:Session,
        user:User,
        conversation_data : ConversationCreate
) -> Conversation :
    conversation = Conversation(
        user_id = user.id,
        title=conversation_data.title or "گفتگوی جدید"

    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def delete_conversation(
        db:Session,
        user:User,
        conversation_id : int
) -> None:
    conversation = db.scalar(
        select(Conversation).where(
            or_(
                conversation.id == conversation_id,
                conversation.user_id == user.id
            )
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="مکالمه پیدا نشد."
        )

    db.delete(conversation)
    db.commit()
    

def get_conversation(
    db:Session,
    user:User,
    conversation_id:int
) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            or_(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="مکالمه پیدا نشد"
        )

    return conversation


def toggle_pin_conversation(
        db:Session,
        user:User,
        conversation_id:int
) -> Conversation:
    conversation = get_conversation(db, user, conversation_id)
    conversation.is_pinned = not conversation.is_pinned
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)

    return conversation

def rename_conversation(
        db:Session,
        user:User,
        conversation_id:int,
        new_title:str,
) -> Conversation:
    conversation = get_conversation(db, user, conversation_id)
    conversation.title = new_title.strip()[:60]
    conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(conversation)

    return conversation


def send_message(
    db: Session,
    user: User,
    conversation_id: int,
    data: MessageCreate
) -> Message:
    conversation = get_conversation(db, user, conversation_id)


    default_titles = ["گفتگوی جدید", "New Chat", ""]
    if conversation.title in default_titles or not conversation.title:
        conversation.title = data.content.strip()[:60]


    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.content,
        has_file=False
    )
    db.add(user_message)


    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="پیامت رو دریافت کردم. به زودی مدل هوش مصنوعی به این بخش اضافه می‌شه.",
        has_file=False
    )
    db.add(assistant_message)

    conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user_message)

    return user_message

