# GenerateData/create_users.py

from Database.database import AsyncSessionLocal
from Database.models import User, UserTool, Tool, Item, UserItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import bcrypt  # For password hashing (install using `pip install bcrypt`)
import asyncio

async def create_user(user_data):
    async with AsyncSessionLocal() as session:
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
                    Tier=1  # Set initial tier as appropriate
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

        except IntegrityError as e:
            await session.rollback()
            print(f"Integrity Error: {e.orig}")
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {e}")
        # No need for a finally block; the async context manager handles session closure

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