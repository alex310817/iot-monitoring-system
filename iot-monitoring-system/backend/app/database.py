import asyncio
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from functools import lru_cache
from fastapi import HTTPException, status

# Загружаем переменные окружения
load_dotenv(override=True)

# Подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

# Async engine with reduced logging and connection pool settings
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Turn off SQL logging
    echo_pool=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,  # Add connection health check
)
async_session_maker = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine with reduced logging
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,  # Turn off SQL logging
    echo_pool=False
)
sync_session_maker = sessionmaker(sync_engine, expire_on_commit=False)

Base = declarative_base()

logger = logging.getLogger(__name__)

# Add database connection check
async def check_db_connection():
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}", exc_info=True)
        return False

# Add proper get_db dependency
async def get_db():
    async with async_session_maker() as session:
        try:
            # Check connection before yielding
            if not await check_db_connection():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection error"
                )
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()

# Функция для создания таблиц
async def init_db():
    async with async_engine.begin() as conn:
        print(f"📡 Подключение к базе данных: {DATABASE_URL}")
        print("📜 Определенные таблицы перед созданием:", Base.metadata.tables.keys())
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы успешно созданы!")

# Запускаем создание таблиц
if __name__ == "__main__":
    asyncio.run(init_db())
