from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


_USERNAME_RE = r"[a-zA-Z0-9_.-]{3,30}"


def _strip_or_none(value: str | None) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    phone_number: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)
    education_level: str | None = Field(default=None, max_length=80)
    field_of_study: str | None = Field(default=None, max_length=120)
    activity_field: str | None = Field(default=None, max_length=120)
    allow_data_usage: bool = False

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("نام و نام خانوادگی الزامی است")
        return value

    @field_validator("education_level", "field_of_study", "activity_field", mode="before")
    @classmethod
    def normalize_optional(cls, value):
        return _strip_or_none(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(_USERNAME_RE, value):
            raise ValueError(
                "Username can only contain letters, numbers, _, ., and -"
            )
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        from app.validation import normalize_iran_phone 
        return normalize_iran_phone(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")
        return value


class UserLogin(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str | None
    last_name: str | None
    display_name: str | None
    avatar_url: str | None
    education_level: str | None
    field_of_study: str | None
    activity_field: str | None
    allow_data_usage: bool
    is_verified: bool
    is_admin: bool
    is_superadmin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    display_name: str | None = Field(default=None, max_length=80)
    username: str | None = Field(default=None, min_length=3, max_length=30)
    email: EmailStr | None = None
    education_level: str | None = Field(default=None, max_length=80)
    field_of_study: str | None = Field(default=None, max_length=120)
    activity_field: str | None = Field(default=None, max_length=120)
    allow_data_usage: bool | None = None

    @field_validator(
        "first_name",
        "last_name",
        "display_name",
        "education_level",
        "field_of_study",
        "activity_field",
        mode="before",
    )
    @classmethod
    def normalize_optional(cls, value):
        return _strip_or_none(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not re.fullmatch(_USERNAME_RE, value):
            raise ValueError(
                "یوزرنیم فقط می‌تواند حروف انگلیسی، عدد، _ ، . و - باشد"
            )
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not any(char.isalpha() for char in value):
            raise ValueError("رمز عبور باید شامل حرف باشد")
        if not any(char.isdigit() for char in value):
            raise ValueError("رمز عبور باید شامل عدد باشد")
        return value
