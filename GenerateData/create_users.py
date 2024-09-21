# GenerateData/create_users.py

from Database.database import SessionLocal
from Database.models import User, UserTool, Tool
from sqlalchemy.exc import IntegrityError
import uuid
import bcrypt  # For password hashing (install using `pip install bcrypt`)

def create_user(user_data):
    db = SessionLocal()
    try:
        # Hash the password (ensure you have bcrypt installed)
        password = user_data.get('Password')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') if password else None

        # Create the User object
        new_user = User(
            Username=user_data['Username'],
            Email=user_data['Email'],
            Password=hashed_password  # Store hashed password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User '{new_user.Username}' created with ID: {new_user.Id}")

        # Assign initial tools
        initial_tools = ['mining_pickaxe', 'player_ultimate']

        for tool_unique_name in initial_tools:
            tool = db.query(Tool).filter(Tool.UniqueName == tool_unique_name).first()
            if not tool:
                print(f"Tool '{tool_unique_name}' not found in the database.")
                continue
        
            user_tool = UserTool(
                UserId=new_user.Id,
                Username=new_user.Username,
                ToolUniqueName=tool.UniqueName,
                Tier=1  # Set initial tier as appropriate
            )
            db.add(user_tool)
            print(f"Assigned tool '{tool.Name}' to user '{new_user.Username}'.")

        db.commit()

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
    finally:
        db.close()

def create_users_from_csv(csv_filename):
    import csv
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_user(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

if __name__ == "__main__":
    csv_file_path = 'GameData/usersData.csv'  # Adjust the path if necessary
    create_users_from_csv(csv_file_path)