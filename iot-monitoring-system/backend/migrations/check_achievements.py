from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

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

def check_and_fix_achievements():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return

    try:
        db_params = parse_db_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if tables exist
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'achievements'
            );
        """)
        achievements_exist = cur.fetchone()[0]

        if not achievements_exist:
            print("❌ Таблица achievements не существует")
            print("🔄 Запустите python migrations/create_achievements.py")
            return

        # Check number of achievements
        cur.execute("SELECT COUNT(*) FROM achievements;")
        count = cur.fetchone()[0]
        print(f"📊 Количество достижений в базе: {count}")

        if count == 0:
            print("⚠️ Достижения отсутствуют в базе")
            answer = input("Хотите инициализировать достижения? (y/n): ")
            if answer.lower() == 'y':
                print("🔄 Запуск create_achievements.py...")
                os.system("python migrations/create_achievements.py")
            return

        # Print existing achievements
        cur.execute("SELECT name, condition_type, condition_value FROM achievements;")
        achievements = cur.fetchall()
        print("\n🏆 Существующие достижения:")
        for ach in achievements:
            print(f"- {ach[0]} ({ach[1]}: {ach[2]})")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_and_fix_achievements()
