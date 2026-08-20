from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Set these in your environment variables (.env file)
DB_USER = os.getenv("DB_USER", "postgres.twqbhtiaeqthefuoraei")
DB_PASSWORD = os.getenv("DB_PASSWORD", "M0E3ctMcYkzgM2yd")
DB_HOST = os.getenv("DB_HOST", "aws-0-ap-northeast-1.pooler.supabase.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SOCIAL_DB_URL = os.getenv("SOCIAL_DB_URL", "postgresql://social_user:social_password@localhost/social_db")

# Primary Auth DB (Supabase)
auth_engine = create_engine(SQLALCHEMY_DATABASE_URL)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)
Base = declarative_base()

# Secondary Social DB
social_engine = create_engine(SOCIAL_DB_URL)
SocialSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=social_engine)
SocialBase = declarative_base()

def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_social_db():
    db = SocialSessionLocal()
    try:
        yield db
    finally:
        db.close()