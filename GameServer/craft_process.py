# crafting.py

import asyncio
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from Database.models import (
    User, UserItem, UserTool, Tool, Item, CraftingRecipe
)
from Database.database import AsyncSessionLocal
import uuid

async def craft_item(user_identifier: str, output_item_unique_name: str, quantity: int):
    """
    Asynchronous function to handle crafting requests.

    :param user_identifier: UserId (UUID as string) or Username.
    :param output_item_unique_name: UniqueName of the item to craft.
    :param quantity: Quantity of the item to craft.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Retrieve the user
            user_query = select(User).options(
                selectinload(User.tools).selectinload(UserTool.tool),
                selectinload(User.items)
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

            # Step 2: Retrieve the crafting recipes for the output item
            recipe_query = select(CraftingRecipe).filter(
                CraftingRecipe.OutputItemUniqueName == output_item_unique_name
            ).options(
                selectinload(CraftingRecipe.tool)
            )
            recipe_entries_result = await session.execute(recipe_query)
            recipe_entries = recipe_entries_result.scalars().all()

            if not recipe_entries:
                print(f"No crafting recipe found for item '{output_item_unique_name}'.")
                raise HTTPException(status_code=404, detail="Crafting recipe not found.")

            # Get the required tool's UniqueName (assuming it's the same across entries)
            tool_unique_name = recipe_entries[0].ToolUniqueName

            # Step 3: Check if the user has the required tool and it's not occupied
            user_tool = next(
                (ut for ut in user.tools if ut.ToolUniqueName == tool_unique_name and not ut.isOccupied),
                None
            )

            if not user_tool:
                print(f"User does not have the required tool '{tool_unique_name}' or it is occupied.")
                raise HTTPException(status_code=400, detail=f"Tool '{tool_unique_name}' not available.")

            # Step 4: Calculate total input requirements
            total_input_requirements = {}
            for entry in recipe_entries:
                input_item_name = entry.InputItemUniqueName
                total_quantity_needed = entry.InputQuantity * quantity

                total_input_requirements[input_item_name] = total_quantity_needed

            # Step 5: Check if the user has enough input items
            user_items_dict = {ui.UniqueName: ui for ui in user.items}
            missing_items = []

            for input_item_name, total_needed in total_input_requirements.items():
                user_item = user_items_dict.get(input_item_name)
                if not user_item or user_item.Quantity < total_needed:
                    missing_items.append({
                        "item": input_item_name,
                        "required": total_needed,
                        "available": user_item.Quantity if user_item else 0
                    })

            if missing_items:
                print(f"User lacks required input items: {missing_items}")
                missing_items_str = ', '.join([f"{mi['required']} x '{mi['item']}'" for mi in missing_items])
                raise HTTPException(status_code=400, detail=f"Insufficient input items: {missing_items_str}")

            # Step 6: Deduct input items from the user's inventory
            for input_item_name, total_needed in total_input_requirements.items():
                user_item = user_items_dict[input_item_name]
                user_item.Quantity -= total_needed
                session.add(user_item)  # Mark as updated

            # Step 7: Update UserTool for ongoing crafting
            user_tool.isOccupied = True
            user_tool.LastUsed = datetime.now()
            user_tool.OngoingCraftingItemUniqueName = output_item_unique_name
            user_tool.OngoingRemainedQuantity = quantity
            session.add(user_tool)

            # Commit the transaction
            await session.commit()

            print(f"Crafting started for user '{user.Username}': {quantity} x '{output_item_unique_name}' using tool '{tool_unique_name}'.")

            return {"status": "success", "message": "Crafting started."}

        except HTTPException as http_exc:
            await session.rollback()
            print(f"HTTPException during crafting: {http_exc.detail}")
            raise http_exc  # Re-raise to be handled by FastAPI
        except Exception as e:
            await session.rollback()
            print(f"Error during crafting: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")