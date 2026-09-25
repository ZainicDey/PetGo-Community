import os
import psycopg2
from urllib.parse import urlparse

def main():
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.twqbhtiaeqthefuoraei',
        password='M0E3ctMcYkzgM2yd',
        host='aws-0-ap-northeast-1.pooler.supabase.com',
        port=5432
    )
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE social_profile ADD COLUMN pet_type VARCHAR(50) NULL;")
        print("Column pet_type added successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
