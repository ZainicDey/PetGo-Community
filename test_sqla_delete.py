import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import DjangoUser

engine = create_engine("postgresql://postgres.twqbhtiaeqthefuoraei:M0E3ctMcYkzgM2yd@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres")
Session = sessionmaker(bind=engine)
session = Session()

pet = session.query(DjangoUser).filter(DjangoUser.username == 'milo2').first()
if pet:
    try:
        session.query(DjangoUser).filter(DjangoUser.id == pet.id).delete(synchronize_session=False)
        session.flush() # Try to push the delete
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.rollback()
else:
    print("Pet not found.")
