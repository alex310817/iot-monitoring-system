from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.database import get_db, sync_session_maker
from app.models import User, Profile
from app.schemas import UserCreate, Token
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.hash import bcrypt
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging
from sqlalchemy import select, or_
import random
from pydantic import BaseModel

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

router = APIRouter()

# Секретный ключ для JWT
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# SMTP-настройки
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Генерация 4-значного кода
def generate_verification_code():
    return str(random.randint(1000, 9999))

# Обновленная функция отправки email
def send_verification_email(email: str, code: str):
    try:
        # Prepare the email message
        msg = MIMEText(
            f"""
            Здравствуйте!
            
            Ваш код подтверждения для IoT Monitoring: {code}
            
            Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
            """
        )
        msg["Subject"] = "Код подтверждения IoT Monitoring"
        msg["From"] = f"IoT Monitoring <{SMTP_EMAIL}>"
        msg["To"] = email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            logging.info(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
            server.starttls()
            logging.info(f"Logging in as {SMTP_EMAIL}")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            logging.info(f"Sending verification code {code} to {email}")
            server.send_message(msg)
            logging.info("Email sent successfully")
            return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

# Add OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Add get_current_user function
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

# 🔐 Регистрация
@router.post("/auth/register", response_model=dict)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Проверяем существующего пользователя
        result = await db.execute(
            select(User).where(User.email == user.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email уже используется")

        # Создаем пользователя
        verification_code = generate_verification_code()
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=bcrypt.hash(user.password),
            verification_token=verification_code,
            is_verified=False,
            is_active=False
        )

        # Пробуем отправить код
        if not send_verification_email(user.email, verification_code):
            raise HTTPException(
                status_code=500,
                detail="Не удалось отправить код подтверждения. Пожалуйста, проверьте email и попробуйте снова."
            )

        # Сохраняем пользователя только если email отправлен
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {
            "status": "success",
            "message": "Код подтверждения отправлен на ваш email",
            "email": user.email
        }

    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception as e:
        await db.rollback()
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при регистрации. Пожалуйста, попробуйте позже."
        )

class VerificationRequest(BaseModel):
    email: str
    code: str

@router.post("/auth/verify-email")
async def verify_email(verification: VerificationRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(User).where(User.email == verification.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404, 
                detail="Пользователь не найден"
            )

        if user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email уже подтверждён"
            )

        if user.verification_token != verification.code:
            raise HTTPException(
                status_code=400, 
                detail="Неверный код подтверждения"
            )

        user.is_verified = True
        user.is_active = True
        user.verification_token = None

        # Создаем профиль пользователя
        profile = Profile(
            user_id=user.id,
            display_name=user.username
        )
        db.add(profile)
        
        await db.commit()
        await db.refresh(user)

        # Создаем токен для автологина
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "status": "success",
            "message": "Email подтверждён",
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException as he:
        await db.rollback()
        raise he
    except Exception as e:
        await db.rollback()
        logging.error(f"Verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при подтверждении email"
        )

# 🔑 Авторизация (вход)
@router.post("/auth/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(User).where(User.email == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь не найден"
            )

        if not bcrypt.verify(form_data.password, user.hashed_password):  # Use bcrypt directly
            raise HTTPException(
                status_code=400,
                detail="Неверный пароль"
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Email не подтверждён"
            )

        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Use longer expiration
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при входе в систему"
        )

# Add refresh token endpoint
@router.post("/auth/refresh")
async def refresh_token(
    current_token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Try to decode expired token
        payload = jwt.decode(
            current_token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401)
            
        # Get user and create new token
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401)
            
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception:
        raise HTTPException(status_code=401)

# Функция генерации JWT-токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})  
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
