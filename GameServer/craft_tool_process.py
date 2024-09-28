# GameServer/craft_tool_process.py

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from Database.models import (
    User, UserItem, UserTool, Tool, Item, ToolCraftingRecipe
)
from Database.database import AsyncSessionLocal
import uuid

async def craft_tool(user_identifier: str, output_tool_unique_name: str, tier: int):
    """
    Asynchronous function to handle tool crafting requests.

    :param user_identifier: UserId (UUID as string) or Username.
    :param output_tool_unique_name: UniqueName of the tool to craft.
    :param tier: The tier of the tool to craft.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Retrieve the user
            user_query = select(User).options(
                selectinload(User.items),
                selectinload(User.tools).selectinload(UserTool.tool)
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

            # Step 2: Retrieve the tool
            tool_query = select(Tool).filter(
                Tool.UniqueName == output_tool_unique_name,
                Tool.Tier == tier
            )
            tool_result = await session.execute(tool_query)
            tool = tool_result.scalars().one_or_none()

            if not tool:
                print(f"Tool '{output_tool_unique_name}' with Tier {tier} not found in the database.")
                return {"status": "error", "message": f"Tool '{output_tool_unique_name}' with Tier {tier} not found."}

            # Step 3: Retrieve all crafting recipes for the tool and tier
            recipe_query = select(ToolCraftingRecipe).filter(
                ToolCraftingRecipe.OutputToolUniqueName == output_tool_unique_name,
                ToolCraftingRecipe.OutputToolTier == tier
            )
            recipe_result = await session.execute(recipe_query)
            recipes = recipe_result.scalars().all()

            if not recipes:
                print(f"No crafting recipe found for tool '{output_tool_unique_name}' with Tier {tier}.")
                return {"status": "error", "message": "Crafting recipe not found."}

            # Step 4: Check if the user has enough input items
            user_items_dict = {ui.UniqueName: ui for ui in user.items}

            missing_items = []
            for recipe in recipes:
                required_quantity = recipe.InputQuantity
                input_item_name = recipe.InputItemUniqueName
                user_item = user_items_dict.get(input_item_name)

                if not user_item or user_item.Quantity < required_quantity:
                    missing_quantity = required_quantity - (user_item.Quantity if user_item else 0)
                    missing_items.append(f"{missing_quantity} x '{input_item_name}'")

            if missing_items:
                missing_items_str = ', '.join(missing_items)
                print(f"User lacks required input items: {missing_items_str}")
                return {
                    "status": "error",
                    "message": f"Insufficient input items. Missing: {missing_items_str}."
                }

            # Step 5: Deduct input items from the user's inventory
            for recipe in recipes:
                required_quantity = recipe.InputQuantity
                input_item_name = recipe.InputItemUniqueName
                user_item = user_items_dict[input_item_name]
                user_item.Quantity -= required_quantity
                session.add(user_item)  # Mark as updated

            # Step 6: Check user's existing tools
            user_tools_of_type = [
                ut for ut in user.tools if ut.ToolUniqueName == output_tool_unique_name
            ]

            if not tool.isMultipleCraftable:
                # User cannot have multiple instances
                if user_tools_of_type:
                    # Find the existing tool with the highest tier
                    existing_user_tool = max(user_tools_of_type, key=lambda ut: ut.Tier)
                    if tier > existing_user_tool.Tier:
                        # Upgrade the existing tool's Tier
                        existing_user_tool.Tier = tier
                        session.add(existing_user_tool)
                        await session.commit()
                        print(f"User's existing tool '{output_tool_unique_name}' upgraded to Tier {tier}.")
                        return {"status": "success", "message": f"Upgraded tool '{output_tool_unique_name}' to Tier {tier}."}
                    else:
                        print(f"User already has the tool '{output_tool_unique_name}' with Tier {existing_user_tool.Tier}.")
                        return {"status": "error", "message": f"User already has the tool '{output_tool_unique_name}' with equal or higher Tier."}
                else:
                    # User doesn't have the tool yet, create new UserTool
                    new_user_tool = UserTool(
                        UserId=user.Id,
                        Username=user.Username,
                        ToolUniqueName=output_tool_unique_name,
                        Tier=tier,
                        AcquiredAt=datetime.now(),
                        isEnabled=True
                    )
                    session.add(new_user_tool)
                    await session.commit()
                    print(f"User '{user.Username}' crafted tool '{output_tool_unique_name}' at Tier {tier}.")
                    return {"status": "success", "message": f"Crafted tool '{output_tool_unique_name}' at Tier {tier}."}
            else:
                # Tool is multiple craftable
                current_count = len(user_tools_of_type)
                if tool.maxCraftingNumber is not None and current_count >= tool.maxCraftingNumber:
                    print(f"User already has maximum number ({tool.maxCraftingNumber}) of '{output_tool_unique_name}'.")
                    return {"status": "error", "message": f"Cannot craft more than {tool.maxCraftingNumber} instances of '{output_tool_unique_name}'."}
                else:
                    # Create new UserTool
                    new_user_tool = UserTool(
                        UserId=user.Id,
                        Username=user.Username,
                        ToolUniqueName=output_tool_unique_name,
                        Tier=tier,
                        AcquiredAt=datetime.now(),
                        isEnabled=True
                    )
                    session.add(new_user_tool)
                    await session.commit()
                    print(f"User '{user.Username}' crafted tool '{output_tool_unique_name}' at Tier {tier}.")
                    return {"status": "success", "message": f"Crafted tool '{output_tool_unique_name}' at Tier {tier}."}

        except Exception as e:
            await session.rollback()
            print(f"Error during tool crafting: {e}")
            return {"status": "error", "message": str(e)}