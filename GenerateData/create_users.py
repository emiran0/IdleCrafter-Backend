# GenerateData/create_users.py

from Database.database import AsyncSessionLocal
from Database.models import User, UserTool, Tool, Item, UserItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from passlib.context import CryptContext
import asyncio

class UserAlreadyExistsError(Exception):
    """Exception raised when a username or email is already taken."""
    pass

async def create_user(user_data):
    async with AsyncSessionLocal() as session:
        try:
            # Check if the username already exists
            result = await session.execute(
                select(User).filter(User.Username == user_data['Username'])
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise UserAlreadyExistsError(f"Username '{user_data['Username']}' is already taken.")

            # Check if the email already exists
            result = await session.execute(
                select(User).filter(User.Email == user_data['Email'])
            )
            existing_email = result.scalar_one_or_none()
            if existing_email:
                raise UserAlreadyExistsError(f"Email '{user_data['Email']}' is already registered.")

            # Hash the password
            password = user_data.get('Password')
            pwd_context = CryptContext(schemes=["bcrypt"])
            hashed_password = pwd_context.hash(password)

            # Create the User object
            new_user = User(
                Username=user_data['Username'],
                Email=user_data['Email'],
                Password=hashed_password
            )

            session.add(new_user)
            await session.flush()  # Ensure new_user.Id is available

            # Assign initial tool
            initial_tools = ['player_ultimate']

            for tool_unique_name in initial_tools:
                result = await session.execute(
                    select(Tool).filter(Tool.UniqueName == tool_unique_name)
                )
                tool = result.scalar_one_or_none()
                if not tool:
                    print(f"Tool '{tool_unique_name}' not found in the database.")
                    continue

                user_tool = UserTool(
                    UserId=new_user.Id,
                    Username=new_user.Username,
                    ToolUniqueName=tool.UniqueName,
                    ToolId=1,
                    Tier=1,

                )
                session.add(user_tool)
                print(f"Assigned tool '{tool.Name}' to user '{new_user.Username}'.")

            # Assign initial items
            initial_items = {'mining_stone': 10}

            for item_unique_name, quantity in initial_items.items():
                result = await session.execute(
                    select(Item).filter(Item.UniqueName == item_unique_name)
                )
                item = result.scalar_one_or_none()
                if not item:
                    print(f"Item '{item_unique_name}' not found in the database.")
                    continue

                user_item = UserItem(
                    UserId=new_user.Id,
                    Username=new_user.Username,
                    UniqueName=item.UniqueName,
                    Quantity=quantity
                )
                session.add(user_item)
                print(f"Assigned item '{item.Name}' x{quantity} to user '{new_user.Username}'.")

            await session.commit()
            await session.refresh(new_user)
            print(f"User '{new_user.Username}' created with ID: {new_user.Id}")

            # Return the new user object
            return new_user

        except UserAlreadyExistsError as e:
            await session.rollback()
            print(str(e))
            raise  # Re-raise the exception
        except IntegrityError as e:
            await session.rollback()
            print(f"Integrity Error: {e.orig}")
            raise
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {e}")
            raise

async def create_users_from_csv(csv_filename):
    import csv
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                await create_user(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

if __name__ == "__main__":
    csv_file_path = 'GameData/usersData.csv'  # Adjust the path if necessary
    asyncio.run(create_users_from_csv(csv_file_path))