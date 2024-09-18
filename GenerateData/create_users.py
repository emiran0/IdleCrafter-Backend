# create_users.py

from Database.database import SessionLocal
from Database.models import User
from passlib.context import CryptContext
from datetime import datetime
import uuid

# Initialize the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"])

def create_user(user_data):
    """
    Create a new user in the database from a dictionary input.

    Parameters:
        user_data (dict): A dictionary containing user information.
            Required keys: 'Username', 'Email', 'Password'
            Optional keys: 'Gold', 'Energy', 'TotalLevel'

    Returns:
        User: The created User object.
    """
    db = SessionLocal()
    try:
        # Check for required fields
        required_fields = {'Username', 'Email', 'Password'}
        if not required_fields.issubset(user_data.keys()):
            missing = required_fields - user_data.keys()
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Hash the password
        hashed_password = pwd_context.hash(user_data['Password'])

        # Create the User object
        new_user = User(
            Id=uuid.uuid4(),
            Username=user_data['Username'],
            Email=user_data['Email'],
            Password=hashed_password,
            UserCreatedAt=datetime.now(),
            Gold=user_data.get('Gold', 10.0),
            Energy=user_data.get('Energy', 100.0),
            TotalLevel=user_data.get('TotalLevel', 1)
        )

        # Add the user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"User '{new_user.Username}' created with ID: {new_user.Id}")
        return new_user

    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        raise
    finally:
        db.close()

def create_users_from_dicts(user_dicts):
    """
    Create multiple users from a list of dictionaries.

    Parameters:
        user_dicts (list): A list of dictionaries containing user data.

    Returns:
        list: A list of created User objects.
    """
    created_users = []
    for user_data in user_dicts:
        try:
            user = create_user(user_data)
            created_users.append(user)
        except Exception as e:
            print(f"Failed to create user '{user_data.get('Username')}': {e}")
    return created_users

if __name__ == "__main__":
    # Example usage
    single_user_data = {
        'Username': 'Emirhan',
        'Email': 'emirhan@example.com',
        'Password': 'SecurePassword123',
        'Gold': 5150.0,
        'Energy': 4150.0,
        'TotalLevel': 8
    }

    # Create a single user
    create_user(single_user_data)

    # Example of creating multiple users
    users_data = [
        {
            'Username': 'Mehmet',
            'Email': 'mehmet@example.com',
            'Password': 'AnotherSecurePass456',
            'Gold': 30.0,
            'Energy': 120.0,
            'TotalLevel': 3
        },
        {
            'Username': 'Berke',
            'Email': 'berke@example.com',
            'Password': 'YetAnotherPass789',
            # Gold, Energy, and TotalLevel will use default values
        },
        {
            'Username': 'Gokhan',
            'Email': 'gokhan@example.com',
            'Password': 'SuperSecure'
        }
    ]

    # Create multiple users
    create_users_from_dicts(users_data)