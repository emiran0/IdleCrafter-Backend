# crafting_process.py

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from Database.models import (
    User, UserItem, UserTool, Tool, Item, CraftingRecipe, UserCategoryXP, CategoryLevels
)
from Database.database import AsyncSessionLocal

async def crafting_ongoing_process():
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Fetch all occupied UserTools
            ongoing_tools_query = select(UserTool).options(
                selectinload(UserTool.user),
                selectinload(UserTool.tool),
                selectinload(UserTool.ongoing_crafting_item)
            ).filter(
                UserTool.isOccupied == True
            )
            result = await session.execute(ongoing_tools_query)
            ongoing_tools = result.scalars().all()

            current_time = datetime.now()

            # Pre-fetch all CategoryLevels and organize them by category
            category_levels_query = select(CategoryLevels)
            category_levels_result = await session.execute(category_levels_query)
            all_category_levels = category_levels_result.scalars().all()

            # Organize CategoryLevels by category
            category_levels_dict = {}
            for level in all_category_levels:
                if level.Category not in category_levels_dict:
                    category_levels_dict[level.Category] = []
                category_levels_dict[level.Category].append(level)

            # Sort levels for each category
            for levels in category_levels_dict.values():
                levels.sort(key=lambda l: l.Level)

            for user_tool in ongoing_tools:
                user = user_tool.user
                tool = user_tool.tool
                item = user_tool.ongoing_crafting_item  # The item being crafted
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

                    # Output item multiplier
                    output_multiplier = recipe_entries[0].OutputQuantity

                    if user_item:
                        user_item.Quantity += crafted_quantity * output_multiplier
                    else:
                        # Create new UserItem
                        user_item = UserItem(
                            UserId=user.Id,
                            Username=user.Username,
                            UniqueName=crafting_item_name,
                            Quantity=crafted_quantity * output_multiplier
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

                    # --- XP Yielding Functionality ---
                    xp_yield = item.XPYield or 0
                    xp_to_add = crafted_quantity * output_multiplier * xp_yield

                    category = item.Category

                    # Fetch all UserCategoryXP entries for the user
                    user_category_xp_query = select(UserCategoryXP).filter(
                        UserCategoryXP.UserId == user.Id
                    )
                    user_category_xp_result = await session.execute(user_category_xp_query)
                    user_category_xp_list = user_category_xp_result.scalars().all()
                    user_category_xp_dict = {ucxp.Category: ucxp for ucxp in user_category_xp_list}

                    # Fetch or create UserCategoryXP entry for the user and category
                    user_category_xp = user_category_xp_dict.get(category)

                    if not user_category_xp:
                        # Create new UserCategoryXP
                        user_category_xp = UserCategoryXP(
                            UserId=user.Id,
                            Username=user.Username,
                            Category=category,
                            CurrentXP=0,
                            CategoryLevel=1,
                            LastUpdated=datetime.now()
                        )
                        session.add(user_category_xp)
                        user_category_xp_dict[category] = user_category_xp  # Update the dict

                    # Update CurrentXP
                    user_category_xp.CurrentXP += xp_to_add
                    user_category_xp.LastUpdated = datetime.now()

                    # Check for level-up
                    category_levels = category_levels_dict.get(category, [])

                    # Determine new level based on CurrentXP
                    new_level = user_category_xp.CategoryLevel
                    for level in category_levels:
                        if user_category_xp.CurrentXP >= level.StartingXp:
                            new_level = level.Level
                        else:
                            break

                    level_up_occurred = False
                    if new_level > user_category_xp.CategoryLevel:
                        user_category_xp.CategoryLevel = new_level
                        print(f"User '{user.Username}' leveled up in category '{category}' to level {new_level}.")
                        level_up_occurred = True

                    # Add user_category_xp to session
                    session.add(user_category_xp)

                    # --- Update TotalLevel if Level-Up Occurred ---
                    if level_up_occurred:
                        # Directly query the database to sum up all category levels for the user
                        total_category_levels_result = await session.execute(
                            select(func.sum(UserCategoryXP.CategoryLevel)).filter(
                                UserCategoryXP.UserId == user.Id
                            )
                        )
                        total_category_levels = total_category_levels_result.scalar() or 0

                        # Update the user's TotalLevel
                        user.TotalLevel = total_category_levels
                        session.add(user)
                    # --- End of TotalLevel Update ---
                    # --- End of XP Yielding Functionality ---

            # Commit all changes
            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"Error processing ongoing crafting: {e}")


# async def schedule_crafting_processing(interval_seconds: int):
#     while True:
#         await process_ongoing_crafting()
#         await asyncio.sleep(interval_seconds)

# if __name__ == "__main__":
#     asyncio.run(schedule_crafting_processing(5))  # Run every 60 seconds