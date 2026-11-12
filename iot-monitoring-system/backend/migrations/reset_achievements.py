from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def reset_achievements():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return

    try:
        db_params = parse_db_url(DATABASE_URL)
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Delete all achievements
        print("🗑️ Удаление старых достижений...")
        cur.execute("DELETE FROM user_achievements;")
        cur.execute("DELETE FROM achievements;")
        
        print("✅ Достижения успешно удалены")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при удалении достижений: {e}")

if __name__ == "__main__":
    reset_achievements()
