import os
import psycopg2

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
        # Find a pet user
        cur.execute("SELECT u.id, u.username FROM auth_user u JOIN social_profile sp ON u.id = sp.user_id WHERE sp.profile_type = 'pet' LIMIT 1;")
        pet = cur.fetchone()
        if pet:
            print(f"Found pet: {pet[1]} (ID: {pet[0]})")
            try:
                # Let's try to delete it inside a transaction to see if it fails
                conn.autocommit = False
                cur.execute("DELETE FROM auth_user WHERE id = %s;", (pet[0],))
                conn.rollback() # rollback immediately so we don't actually delete it
                print("Delete query succeeded without constraint errors.")
            except Exception as inner_e:
                conn.rollback()
                print(f"Delete query failed with error: {inner_e}")
        else:
            print("No pet profile found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
