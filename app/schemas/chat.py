from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict




class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    has_file: bool
    file_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class ConversationCreate(BaseModel):
    title: str = Field(default="گفتگوی جدید", min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    id: int
    public_id : str
    title: str
    created_at: datetime
    updated_at: datetime
    is_pinned : bool

    model_config = ConfigDict(from_attributes=True)

class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []