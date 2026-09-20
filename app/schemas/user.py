from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30
    )
    email : EmailStr
    password : str = Field(
        min_length=3,
        max_length=128
    )


    @field_validator("username")
    @classmethod
    def validate_username(cls, value:str) -> str:
        value = value.strip()

        if not re.fullmatch(
            r"[a-zA-Z0-9_.-]{3,30}",
            value
        ):
            raise ValueError(
                "Username can only contain letters, numbers, _, ., and -"
            )

        return value


    @field_validator("email")
    @classmethod
    def normalize_email(cls, value:EmailStr) -> str:
        return str(value).strip().lower()


    @field_validator("password")
    @classmethod
    def validate_password(cls, value:str) -> str:
        if not any(char.isalpha() for char in value):
            raise ValueError(
                "Password must contain at least one letter"
            )

        if not any(char.isdigit() for char in value):
                raise ValueError(
                    "Password must contain at least one number"
                )
        return value



class UserLogin(BaseModel):
    email:str
    password:str = Field(
        min_length=1,
        max_length=128
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()



class UserResponse(BaseModel):
    id : int
    username : str
    email : str
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: str | None
    avatar_url: str | None
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    username: str | None = Field(default=None, min_length=3, max_length=30)


    @field_validator("username")
    @classmethod
    def validate_username(cls, v:str | None) -> str | None:
        if v is None:
            return v
        v.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_]+", v):
            raise ValueError("یوزرنیم فقط می‌تواند حروف انگلیسی، عدد و _ باشد")
        return v



class PasswordChange(BaseModel):
    current_password: str = Field(... ,min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)



    