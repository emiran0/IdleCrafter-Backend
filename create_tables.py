# create_tables.py

from Database.database import engine, Base
import Database.models  # Ensure models are imported so they are registered

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()