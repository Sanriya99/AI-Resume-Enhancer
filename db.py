import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# For a quick local run, SQLite is used unless DATABASE_URL is configured.
# For TiDB Cloud, set DATABASE_URL in your .env file to a mysql+pymysql URL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///resume.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
