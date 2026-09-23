import os
import psycopg2
from urllib.parse import urlparse

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
    cur.execute("""
        SELECT tc.constraint_name, rc.delete_rule 
        FROM information_schema.table_constraints tc 
        JOIN information_schema.referential_constraints rc 
          ON tc.constraint_name = rc.constraint_name 
        WHERE tc.table_name IN ('follows');
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"Constraint: {r[0]} | Delete Rule: {r[1]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
