from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TicketReplyOut(BaseModel):
    id: int
    author_id: int
    author_role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketListItem(BaseModel):
    id: int
    category: str
    description: str
    status: str
    attachment_url: str | None = None
    username: str | None = None
    email: str | None = None
    created_at: datetime
    updated_at: datetime
    reply_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketListItem):
    replies: list[TicketReplyOut] = []


class AdminTicketReplyCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class AdminTicketStatusUpdate(BaseModel):
    status: str = Field(...)
