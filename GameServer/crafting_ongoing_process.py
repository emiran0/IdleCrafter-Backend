# crafting_process.py

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from Database.models import (
    User, UserItem, UserTool, Tool, Item, CraftingRecipe
)
from Database.database import AsyncSessionLocal

async def process_ongoing_crafting():
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Fetch all occupied UserTools
            ongoing_tools_query = select(UserTool).options(
                selectinload(UserTool.user),
                selectinload(UserTool.tool)
            ).filter(
                UserTool.isOccupied == True
            )
            result = await session.execute(ongoing_tools_query)
            ongoing_tools = result.scalars().all()

            current_time = datetime.now()

            for user_tool in ongoing_tools:
                user = user_tool.user
                tool = user_tool.tool
                crafting_item_name = user_tool.OngoingCraftingItemUniqueName
                remaining_quantity = user_tool.OngoingRemainedQuantity
                last_used = user_tool.LastUsed

                # Calculate elapsed time
                elapsed_time = (current_time - last_used).total_seconds()

                # Fetch the GenerationDuration from CraftingRecipe
                recipe_query = select(CraftingRecipe).filter(
                    CraftingRecipe.ToolUniqueName == tool.UniqueName,
                    CraftingRecipe.OutputItemUniqueName == crafting_item_name
                )
                recipe_result = await session.execute(recipe_query)
                recipe_entries = recipe_result.scalars().all()

                if not recipe_entries:
                    print(f"No crafting recipe found for tool '{tool.UniqueName}' and item '{crafting_item_name}'.")
                    continue

                # Assume GenerationDuration is the same across entries
                generation_duration = recipe_entries[0].GenerationDuration

                # Calculate how many items have been crafted
                crafted_quantity = int(elapsed_time // generation_duration)

                if crafted_quantity > 0:
                    # Ensure we don't craft more than the remaining quantity
                    crafted_quantity = min(crafted_quantity, remaining_quantity)

                    # Step 3: Update user's inventory
                    user_items_query = select(UserItem).filter(
                        UserItem.UserId == user.Id,
                        UserItem.UniqueName == crafting_item_name
                    )
                    user_item_result = await session.execute(user_items_query)
                    user_item = user_item_result.scalars().one_or_none()

                    if user_item:
                        user_item.Quantity += crafted_quantity
                    else:
                        # Create new UserItem
                        user_item = UserItem(
                            UserId=user.Id,
                            Username=user.Username,
                            UniqueName=crafting_item_name,
                            Quantity=crafted_quantity
                        )
                        session.add(user_item)

                    # Step 4: Update UserTool
                    user_tool.OngoingRemainedQuantity -= crafted_quantity

                    if user_tool.OngoingRemainedQuantity <= 0:
                        # Crafting is complete
                        user_tool.isOccupied = False
                        user_tool.OngoingCraftingItemUniqueName = None
                        user_tool.OngoingRemainedQuantity = None
                        user_tool.LastUsed = None
                        print(f"Crafting completed for user '{user.Username}': '{crafting_item_name}'")
                    else:
                        # Update LastUsed to the time after the crafted items have been produced
                        time_consumed = crafted_quantity * generation_duration
                        user_tool.LastUsed = last_used + timedelta(seconds=time_consumed)

                    # Add updates to the session
                    session.add(user_item)
                    session.add(user_tool)

            # Commit all changes
            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"Error processing ongoing crafting: {e}")


async def schedule_crafting_processing(interval_seconds: int):
    while True:
        await process_ongoing_crafting()
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(schedule_crafting_processing(5))  # Run every 60 seconds