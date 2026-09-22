from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AdminStatsSeries(BaseModel):
    months: list[str] = []
    new_users: list[int] = []
    chats: list[int] = []
    active_users: list[int] = []


class AdminStats(BaseModel):
    users_total: int
    users_today: int
    users_active: int
    conversations_total: int
    messages_total: int
    documents_total: int
    subscribers_active: int = 0
    series: AdminStatsSeries = Field(default_factory=AdminStatsSeries)


class AdminUserListItem(BaseModel):
    id: int
    username: str
    email: str
    display_name: str | None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    is_admin: bool
    is_superadmin: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None  # فقط superadmin


class AdminConversationItem(BaseModel):
    id: int
    public_id: str | None = None
    title: str
    user_id: int
    username: str | None = None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminMessageItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminConversationDetail(AdminConversationItem):
    messages: list[AdminMessageItem] = []


class AdminDocumentItem(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size: int
    user_id: int
    username: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)