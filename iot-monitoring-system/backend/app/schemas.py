from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    email: str
    password: str

    @field_validator('username')
    def username_validator(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Username должен быть не короче 3 символов')
        return v

    @field_validator('password')
    def password_validator(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Пароль должен быть не короче 6 символов')
        return v

    @field_validator('email')
    def email_validator(cls, v):
        if '@' not in v:
            raise ValueError('Некорректный email')
        return v.lower()

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DeviceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: bool = False
    owner_id: Optional[int] = None  # Make owner_id optional

class DeviceControl(BaseModel):
    action: str  # "on" или "off"

class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    status: bool
    last_update: Optional[datetime] = None

class SensorDataCreate(BaseModel):
    device_id: int
    temperature: float
    humidity: Optional[float] = None

class ProfileUpdate(BaseModel):
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class EmailVerification(BaseModel):
    email: str
    code: str

    @field_validator('code')
    def code_validator(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError('Код должен состоять из 4 цифр')
        return v
