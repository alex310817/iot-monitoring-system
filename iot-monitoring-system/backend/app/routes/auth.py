from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random  # Генерация 6-значного кода

from app.auth import create_access_token, get_password_hash, authenticate_user
from app.database import get_db
from app.models import User
from app.utils.email import send_verification_email

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str

class VerifyCode(BaseModel):
    email: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email уже используется")

    verification_code = str(random.randint(100000, 999999))  # 6-значный код

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_verified=False,
        verification_code=verification_code
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_verification_email(user.email, verification_code)  # Отправляем код

    return {"message": "Код отправлен на email. Введите его для подтверждения."}

@router.post("/verify")
async def verify_email(data: VerifyCode, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Неверный код")

    user.is_verified = True
    user.verification_code = None  # Очищаем код после успешного подтверждения
    db.commit()

    return {"message": "Email подтвержден!"}

@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = authenticate_user(user.email, user.password, db)
    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Подтвердите email перед входом")

    token = create_access_token(data={"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
