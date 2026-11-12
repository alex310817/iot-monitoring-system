from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

load_dotenv()

def parse_db_url(url):
    cleaned_url = url.replace("postgresql+asyncpg://", "")
    credentials, location = cleaned_url.split("@")
    user, password = credentials.split(":")
    host_port, dbname = location.split("/")
    host, port = host_port.split(":")
    return {
        "dbname": dbname,
        "user": user,
        "password": password,
        "host": host,
        "port": port
    }

def create_achievements_tables():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return

    try:
        db_params = parse_db_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create achievements table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                description VARCHAR NOT NULL,
                icon VARCHAR NOT NULL,
                condition_type VARCHAR NOT NULL,
                condition_value INTEGER NOT NULL
            );
        """)

        # Create user_achievements table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                achievement_id INTEGER REFERENCES achievements(id),
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 0
            );
        """)

        # Insert default achievements
        default_achievements = [
            # Существующие достижения
            ("Первые шаги", "Добавьте первое устройство", "DevicesOther", "devices_added", 1),
            ("Коллекционер", "Добавьте 5 устройств", "Collections", "devices_added", 5),
            ("Личность", "Заполните информацию профиля", "Person", "profile_completed", 1),
            ("Фотограф", "Установите аватар профиля", "PhotoCamera", "avatar_set", 1),
            
            # Управление устройствами
            ("Мастер автоматизации", "Добавьте 10 устройств", "SmartToy", "devices_added", 10),
            ("Технический гений", "Добавьте 20 устройств", "Psychology", "devices_added", 20),
            ("Первое включение", "Включите устройство впервые", "PowerSettingsNew", "device_switched", 1),
            ("Активный пользователь", "Переключите устройства 50 раз", "TouchApp", "device_switched", 50),
            ("Энергетик", "Переключите устройства 100 раз", "Bolt", "device_switched", 100),
            ("Ночной режим", "Управляйте устройствами ночью", "Brightness3", "night_control", 1),
            
            # Профиль и персонализация
            ("Биограф", "Заполните био более 100 символов", "Description", "bio_length", 100),
            ("Дизайнер", "Установите фон профиля", "Wallpaper", "background_set", 1),
            ("Стилист", "Измените аватар 5 раз", "Style", "avatar_changed", 5),
            ("Художник", "Загрузите 10 разных фонов", "Palette", "backgrounds_changed", 10),
            
            # Активность
            ("Новичок", "Проведите в системе 1 час", "Schedule", "time_spent", 1),
            ("Постоянный пользователь", "Проведите в системе 24 часа", "AccessTime", "time_spent", 24),
            ("Эксперт", "Проведите в системе 168 часов", "AccessTimeFilled", "time_spent", 168),
            ("Ежедневный визит", "Войдите в систему 7 дней подряд", "CalendarToday", "daily_login", 7),
            ("Преданный пользователь", "Войдите в систему 30 дней подряд", "EventAvailable", "daily_login", 30),
            
            # Мониторинг
            ("Наблюдатель", "Просмотрите статистику устройства", "Timeline", "stats_viewed", 1),
            ("Аналитик", "Просмотрите статистику 100 раз", "Analytics", "stats_viewed", 100),
            ("Температурный контроль", "Отследите изменение температуры", "Thermostat", "temperature_monitored", 1),
            ("Метеоролог", "Отслеживайте температуру 24 часа", "Cloud", "temperature_monitored", 24),
            
            # Безопасность
            ("Хранитель", "Включите двухфакторную аутентификацию", "Security", "2fa_enabled", 1),
            ("Страж", "Измените пароль", "Lock", "password_changed", 1),
            ("Защитник", "Проверьте историю входов", "VerifiedUser", "login_history_checked", 1),
            
            # Социальные
            ("Первые шаги в команде", "Добавьте первого пользователя в команду", "Group", "team_member_added", 1),
            ("Командный игрок", "Добавьте 5 пользователей в команду", "Groups", "team_member_added", 5),
            ("Организатор", "Создайте группу устройств", "FolderSpecial", "device_group_created", 1),
            
            # Особые достижения
            ("Ночной страж", "Управляйте устройствами в 3 часа ночи", "NightlightRound", "night_owl", 1),
            ("Утренняя пташка", "Управляйте устройствами в 6 утра", "WbSunny", "early_bird", 1),
            ("Новогодний администратор", "Управляйте устройствами 1 января", "Celebration", "new_year_control", 1),
            ("Властелин автоматизации", "Создайте 10 сценариев", "AutoMode", "scenarios_created", 10),
            ("Мастер сценариев", "Активируйте сценарий 100 раз", "AutoAwesome", "scenarios_activated", 100),
        ]

        cur.execute("SELECT COUNT(*) FROM achievements")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
                INSERT INTO achievements (name, description, icon, condition_type, condition_value)
                VALUES (%s, %s, %s, %s, %s)
            """, default_achievements)

        print("✅ Successfully created achievement tables and inserted default achievements")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_achievements_tables()
