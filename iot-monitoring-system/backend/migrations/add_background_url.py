from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

def parse_db_url(url):
    # Remove postgresql+asyncpg:// and split remaining
    cleaned_url = url.replace("postgresql+asyncpg://", "")
    # Split user:pass@host:port/dbname
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

def add_background_url_column():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return

    try:
        # Parse database URL
        db_params = parse_db_url(DATABASE_URL)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Add the column
        cur.execute("""
            ALTER TABLE profiles 
            ADD COLUMN IF NOT EXISTS background_url VARCHAR;
        """)
        
        print("✅ Successfully added background_url column")
        
        # Close connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_background_url_column()
