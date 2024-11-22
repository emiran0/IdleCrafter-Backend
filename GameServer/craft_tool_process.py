# GameServer/craft_tool_process.py

import asyncio
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, func
from Database.models import (
    User, UserItem, UserTool, Tool, Item, ToolCraftingRecipe, UserCategoryXP, CategoryLevels
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
                selectinload(User.tools).selectinload(UserTool.tool),
                selectinload(User.category_xp)  # Load user's category XP
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
                raise HTTPException(status_code=404, detail="User not found.")

            # Step 2: Retrieve the tool
            tool_query = select(Tool).filter(
                Tool.UniqueName == output_tool_unique_name,
                Tool.Tier == tier
            )
            tool_result = await session.execute(tool_query)
            tool = tool_result.scalars().one_or_none()

            if not tool:
                print(f"Tool '{output_tool_unique_name}' with Tier {tier} not found in the database.")
                raise HTTPException(status_code=404, detail=f"Tool '{output_tool_unique_name}' with Tier {tier} not found.")

            # Step 3: Retrieve all crafting recipes for the tool and tier
            recipe_query = select(ToolCraftingRecipe).filter(
                ToolCraftingRecipe.OutputToolUniqueName == output_tool_unique_name,
                ToolCraftingRecipe.OutputToolTier == tier
            )
            recipe_result = await session.execute(recipe_query)
            recipes = recipe_result.scalars().all()

            if not recipes:
                print(f"No crafting recipe found for tool '{output_tool_unique_name}' with Tier {tier}.")
                raise HTTPException(status_code=404, detail="Crafting recipe not found.")

            # --- Start of Level Check Addition ---
            # Assume all recipes for this tool and tier have the same Category and MinimumCategoryLevel
            recipe = recipes[0]
            required_category = recipe.Category
            minimum_category_level = recipe.MinimumCategoryLevel or 0

            # Fetch user's level in the required category
            user_category_xp = next((UserCategoryXP for UserCategoryXP in user.category_xp if UserCategoryXP.Category == required_category), None)
            user_category_level = user_category_xp.CategoryLevel if user_category_xp else 0

            if user_category_level < minimum_category_level:
                print(f"User does not meet the minimum category level requirement for category '{required_category}'.")
                raise HTTPException(
                    status_code=400,
                    detail=f"Minimum level {minimum_category_level} required in category '{required_category}'. Your level: {user_category_level}."
                )
            # --- End of Level Check Addition ---

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
                raise HTTPException(status_code=400, detail=f"Missing required input items: {missing_items_str}")

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
                        raise HTTPException(status_code=400, detail=f"User already has the tool '{output_tool_unique_name}' with equal or higher Tier.")
                else:
                    # User doesn't have the tool yet, create new UserTool
                    new_user_tool = UserTool(
                        UserId=user.Id,
                        Username=user.Username,
                        ToolUniqueName=output_tool_unique_name,
                        ToolId=1,
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
                    raise HTTPException(status_code=400, detail=f"Cannot craft more than {tool.maxCraftingNumber} instances of '{output_tool_unique_name}'.")
                else:
                    # Determine next MultipleToolId
                    existing_multiple_ids = [ut.ToolId for ut in user_tools_of_type]
                    next_multiple_tool_id = max(existing_multiple_ids, default=0) + 1

                    # Create new UserTool
                    new_user_tool = UserTool(
                        UserId=user.Id,
                        Username=user.Username,
                        ToolUniqueName=output_tool_unique_name,
                        ToolId=next_multiple_tool_id,
                        Tier=tier,
                        AcquiredAt=datetime.utcnow(),
                        isEnabled=True
                    )
                    session.add(new_user_tool)
                    await session.commit()
                    print(f"User '{user.Username}' crafted tool '{output_tool_unique_name}' at Tier {tier}.")
                    return {"status": "success", "message": f"Crafted tool '{output_tool_unique_name}' at Tier {tier}."}

        except HTTPException as http_exc:
            await session.rollback()
            print(f"HTTPException during tool crafting: {http_exc.detail}")
            raise http_exc  # Re-raise to be handled by FastAPI
        except Exception as e:
            await session.rollback()
            print(f"Error during tool crafting: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")