# Database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
DB_URL = os.getenv("DB_URL")

# For PostgreSQL, it would be something like:
DATABASE_URL = DB_URL

# Create the engine
engine = create_engine(
    DATABASE_URL,
    # connect_args={"check_same_thread": False}  # Only needed for SQLite
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for your models to inherit
Base = declarative_base()