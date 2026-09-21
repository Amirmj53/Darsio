import uuid
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
        .filter( 
            Conversation.user_id == user.id,
            Conversation.deleted_at.is_(None),

        )
        .order_by(
            Conversation.is_pinned.desc(),
            Conversation.updated_at.desc()
        )
        .all()
    )


def create_conversation(
        db:Session,
        user:User,
        conversation_data : ConversationCreate
) -> Conversation :
    conversation = Conversation(
        user_id = user.id,
        title=conversation_data.title or "گفتگوی جدید",
        public_id = str(uuid.uuid4()),

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
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.deleted_at.is_(None)
        )
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="مکالمه پیدا نشد."
        )
    conversation.deleted_at = datetime.now(timezone.utc)
    db.commit()

def restore_conversation(db:Session, user:User, public_id:str) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == public_id,
            Conversation.user_id == user.id,
            Conversation.deleted_at.is_not(None)
        )
    )

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="مکالمه پیدا نشد")

    conversation.deleted_at = None
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)

    return conversation 

def get_conversation(
    db:Session,
    user:User,
    public_id:str
) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
                Conversation.public_id == public_id,
                Conversation.user_id == user.id,
                Conversation.deleted_at.is_(None),
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
        public_id:str,
) -> Conversation:
    conversation = get_conversation(db, user, public_id)
    conversation.is_pinned = not conversation.is_pinned
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)

    return conversation

def rename_conversation(
        db:Session,
        user:User,
        public_id:str,
        new_title:str,
) -> Conversation:
    conversation = get_conversation(db, user, public_id)
    conversation.title = new_title.strip()[:60]
    conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(conversation)

    return conversation


def send_message(
    db: Session,
    user: User,
    public_id:str,
    data: MessageCreate
) -> Message:
    conversation = get_conversation(db, user, public_id)


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



def search_conversations(db: Session, user: User, query: str) -> list[Conversation]:
    query = query.strip()
    if not query:
        return get_user_conversations(db, user)

    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.deleted_at.is_(None),
            Conversation.title.ilike(f"%{query}%")
        )
        .order_by(
            Conversation.is_pinned.desc(),
            Conversation.updated_at.desc()
        )
        .all()
    )

def edit_message(
    db: Session,
    user: User,
    message_id: int,
    new_content: str
) -> Message:
    message = db.scalar(
        select(Message).where(Message.id == message_id)
    )
    if not message:
        raise HTTPException(status_code=404, detail="پیام پیدا نشد")

    conversation = get_conversation(db, user, message.conversation_id)

    if message.role != "user":
        raise HTTPException(status_code=400, detail="فقط پیام کاربر قابل ویرایش است")

    message.content = new_content.strip()


    db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.created_at > message.created_at,
        Message.role == "assistant"
    ).delete(synchronize_session=False)


    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="پیام ویرایش‌شده دریافت شد. پاسخ جدید بر اساس متن به‌روز تولید شد.",
        has_file=False
    )
    db.add(assistant_message)

    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)
    return message