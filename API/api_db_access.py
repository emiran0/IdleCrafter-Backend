# API/api_db_access.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from Database.database import AsyncSessionLocal
from Database.models import (
    User, UserTool, Tool, UserItem, Item
)

# Function to get user tools
async def fetch_user_tools(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserTool)
            .options(
                selectinload(UserTool.tool)
            )
            .filter(UserTool.UserId == user_id)
        )
        user_tools = result.scalars().all()
    return user_tools

# Function to get user items
async def fetch_user_items(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserItem)
            .options(
                selectinload(UserItem.item)
            )
            .filter(UserItem.UserId == user_id)
        )
        user_items = result.scalars().all()
    return user_items

# Function to get user by username
async def get_user_by_username(username):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).filter(User.Username == username)
        )
        user = result.scalar_one_or_none()
    return user

# Function to toggle the isEnabled status of a user's tool
async def toggle_user_tool_enabled(user_id: str, tool_unique_name: str) -> UserTool:
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the UserTool for the user and tool_unique_name
            result = await session.execute(
                select(UserTool)
                .filter(
                    UserTool.UserId == user_id,
                    UserTool.ToolUniqueName == tool_unique_name
                )
            )
            user_tool = result.scalar_one_or_none()
            
            if not user_tool:
                raise NoResultFound("Tool not found for user")
            
            # Toggle the isEnabled field
            user_tool.isEnabled = not user_tool.isEnabled
            
            # Save changes
            await session.commit()
            await session.refresh(user_tool)
            
            return user_tool
        except Exception as e:
            await session.rollback()
            raise e  # Re-raise exception to be handled by calling function