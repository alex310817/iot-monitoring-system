import asyncio
from app.database import Base, async_engine, sync_session_maker
from app.models import User, Device, Profile, SensorData, Achievement, UserAchievement
from passlib.hash import bcrypt
import sys

async def create_tables():
    async with async_engine.begin() as conn:
        # Проверяем существование таблиц
        result = await conn.run_sync(lambda sync_conn: sync_conn.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """))
        tables_exist = result.scalar()

        if tables_exist:
            if len(sys.argv) > 1 and sys.argv[1] == "--force":
                print("🔄 Пересоздание всех таблиц...")
                await conn.run_sync(Base.metadata.drop_all)
            else:
                print("⚠️ Таблицы уже существуют. Для пересоздания используйте флаг --force")
                return

        print("📦 Создание таблиц...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы успешно созданы!")

async def create_default_admin():
    with sync_session_maker() as session:
        admin = session.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=bcrypt.hash("admin123"),
                is_verified=True,
                is_active=True
            )
            session.add(admin)
            session.flush()

            profile = Profile(
                user_id=admin.id,
                display_name="System Administrator",
                bio="System administrator account"
            )
            session.add(profile)
            session.commit()
            print("✅ Создан аккаунт администратора")
        else:
            print("ℹ️ Аккаунт администратора уже существует")

async def init():
    print("🚀 Инициализация базы данных...")
    await create_tables()
    await create_default_admin()
    print("✅ Инициализация завершена!")

if __name__ == "__main__":
    print("""
⚠️  Внимание! Эта команда инициализирует базу данных.
    Использование:
    - python init_db.py       : Создать таблицы только если их нет
    - python init_db.py --force: Пересоздать все таблицы (удалит существующие данные!)
    """)
    asyncio.run(init())
