# item_craft_process.py

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from Database.models import (
    User, UserItem, UserTool, Tool, Item, ToolCraftingRecipe
)
from Database.database import AsyncSessionLocal
import uuid

async def craft_tool(user_identifier: str, output_tool_unique_name: str):
    """
    Asynchronous function to handle tool crafting requests.

    :param user_identifier: UserId (UUID as string) or Username.
    :param output_tool_unique_name: UniqueName of the tool to craft.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Retrieve the user
            user_query = select(User).options(
                selectinload(User.items),
                selectinload(User.tools)
            )
            try:
                # Try to parse user_identifier as UUID
                user_uuid = uuid.UUID(user_identifier)
                user_query = user_query.filter(User.Id == user_uuid)
            except ValueError:
                # If not UUID, treat as Username
                user_query = user_query.filter(User.Username == user_identifier)

            result = await session.execute(user_query)
            user = result.scalars().one_or_none()

            if not user:
                print("User not found.")
                return {"status": "error", "message": "User not found."}

            # Step 2: Retrieve the tool crafting recipe
            recipe_query = select(ToolCraftingRecipe).filter(
                ToolCraftingRecipe.OutputToolUniqueName == output_tool_unique_name
            )
            recipe_result = await session.execute(recipe_query)
            recipe = recipe_result.scalars().one_or_none()

            if not recipe:
                print(f"No crafting recipe found for tool '{output_tool_unique_name}'.")
                return {"status": "error", "message": "Crafting recipe not found."}

            # Step 3: Check if the user has enough input items
            total_input_requirement = recipe.InputQuantity
            input_item_name = recipe.InputItemUniqueName

            user_items_dict = {ui.UniqueName: ui for ui in user.items}
            user_item = user_items_dict.get(input_item_name)

            if not user_item or user_item.Quantity < total_input_requirement:
                missing_quantity = total_input_requirement - (user_item.Quantity if user_item else 0)
                print(f"User lacks required input item '{input_item_name}': Required {total_input_requirement}, Available {user_item.Quantity if user_item else 0}")
                return {
                    "status": "error",
                    "message": f"Insufficient input items. Missing {missing_quantity} x '{input_item_name}'."
                }

            # Step 4: Deduct input items from the user's inventory
            user_item.Quantity -= total_input_requirement
            session.add(user_item)  # Mark as updated

            # Step 5: Add the crafted tool to the user's tools
            # Check if the user already has the tool
            existing_user_tool = next(
                (ut for ut in user.tools if ut.ToolUniqueName == output_tool_unique_name),
                None
            )

            if existing_user_tool:
                print(f"User already has the tool '{output_tool_unique_name}'.")
                return {"status": "error", "message": f"User already has the tool '{output_tool_unique_name}'."}

            # Create a new UserTool entry
            new_user_tool = UserTool(
                UserId=user.Id,
                Username=user.Username,
                ToolUniqueName=output_tool_unique_name,
                Tier=1,
                AcquiredAt=datetime.now(),
                isEnabled=True
            )
            session.add(new_user_tool)

            # Commit the transaction
            await session.commit()

            print(f"User '{user.Username}' crafted tool '{output_tool_unique_name}'.")
            return {"status": "success", "message": f"Crafted tool '{output_tool_unique_name}'."}

        except Exception as e:
            await session.rollback()
            print(f"Error during tool crafting: {e}")
            return {"status": "error", "message": str(e)}
        

# Example call to craft 'advanced_pickaxe' for user with Username 'player1'
async def main():
    result = await craft_tool(
        user_identifier='efe_latrak',
        output_tool_unique_name='mining_oil_extractor'
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())