# process_repeating_tools.py

from Database.database import SessionLocal
from Database.models import (
    UserTool, Tool, ToolGeneratableItem, Item, UserItem, User,
    UserCategoryXP, CategoryLevels
)
from sqlalchemy.orm import joinedload
from datetime import datetime
import random

def process_repeating_tools():
    xp_multiplier = 1  # For future development, can be modified or made dynamic
    db = SessionLocal()
    try:
        # Fetch all user tools that are repeating and enabled
        user_tools = db.query(UserTool).join(Tool).options(
            joinedload(UserTool.tool).joinedload(Tool.generatable_items).joinedload(ToolGeneratableItem.generated_item),
            joinedload(UserTool.user).joinedload(User.items),
            joinedload(UserTool.user).joinedload(User.category_xp)
        ).filter(
            Tool.isRepeating == True,
            UserTool.isEnabled == True
        ).all()

        # Process each user tool
        for user_tool in user_tools:
            user = user_tool.user
            tool = user_tool.tool

            # Create dictionaries for quick access
            user_items_dict = {ui.UniqueName: ui for ui in user.items}
            user_category_xp_dict = {user_exp.Category: user_exp for user_exp in user.category_xp}

            storage_capacity = tool.StorageCapacity

            for gen_item_assoc in tool.generatable_items:
                item = gen_item_assoc.generated_item
                output_item_quantity = gen_item_assoc.OutputItemQuantity or 1

                # Resource requirement (if any)
                resource_unique_name = gen_item_assoc.ResourceUniqueName
                resource_quantity = gen_item_assoc.ResourceQuantity or 0

                # Check if user has enough resources
                if resource_unique_name and resource_quantity > 0:
                    user_resource = user_items_dict.get(resource_unique_name)
                    if not user_resource or user_resource.Quantity < resource_quantity:
                        print(f"User '{user.Username}' lacks required resource '{resource_unique_name}'.")
                        continue  # Skip to next item

                    # Deduct resource
                    user_resource.Quantity -= resource_quantity
                    db.add(user_resource)

                # Probability check
                probability = (item.Probability or 1.0) * (tool.ProbabilityBoost or 1.0)
                if random.random() <= probability:
                    user_item = user_items_dict.get(item.UniqueName)
                    current_quantity = user_item.Quantity if user_item else 0

                    # Check storage capacity
                    if storage_capacity is not None and current_quantity >= storage_capacity:
                        print(f"Storage capacity reached for '{item.Name}' for user '{user.Username}'.")
                        continue  # Skip adding item

                    # Calculate quantity to add without exceeding storage capacity
                    max_addable_quantity = storage_capacity - current_quantity if storage_capacity is not None else output_item_quantity
                    quantity_to_add = min(output_item_quantity, max_addable_quantity)

                    if user_item:
                        user_item.Quantity += quantity_to_add
                    else:
                        user_item = UserItem(
                            UserId=user.Id,
                            Username=user.Username,
                            UniqueName=item.UniqueName,
                            Quantity=quantity_to_add
                        )
                        db.add(user_item)
                        user_items_dict[item.UniqueName] = user_item  # Update the dict

                    # --- XP Yielding Functionality ---
                    xp_yield = item.XPYield or 0
                    xp_to_add = xp_yield * xp_multiplier

                    category = item.Category
                    user_category_xp = user_category_xp_dict.get(category)

                    if not user_category_xp:
                        # Create new UserCategoryXP entry
                        user_category_xp = UserCategoryXP(
                            UserId=user.Id,
                            Username=user.Username,
                            Category=category,
                            CurrentXP=0,
                            CategoryLevel=1, 
                            LastUpdated=datetime.now()
                        )
                        db.add(user_category_xp)
                        user_category_xp_dict[category] = user_category_xp  # Update the dict

                    # Update XP and LastUpdated
                    user_category_xp.CurrentXP += xp_to_add
                    user_category_xp.LastUpdated = datetime.now()

                    # Check for level upgrade
                    # Fetch CategoryLevels for the category, ordered by Level
                    category_levels = db.query(CategoryLevels).filter_by(
                        Category=category
                    ).order_by(CategoryLevels.Level.asc()).all()

                    # Determine new level based on CurrentXP
                    new_level = user_category_xp.CategoryLevel
                    for level in category_levels:
                        if user_category_xp.CurrentXP >= level.StartingXp:
                            new_level = level.Level
                        else:
                            break

                    if new_level > user_category_xp.CategoryLevel:
                        user_category_xp.CategoryLevel = new_level
                        print(f"User '{user.Username}' leveled up in category '{category}' to level {new_level}.")

                        update_total_level_on_category_level_up(user, user_category_xp_dict)
                        db.add(user)  # Ensure user is added to the session

                    db.add(user_category_xp)
                    # --- End of XP Yielding Functionality ---

            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error processing repeating tools: {e}")
    finally:
        db.close()

def update_total_level_on_category_level_up(user, user_category_xp_dict):
    """
    Updates the user's TotalLevel when a category level increases.

    :param user: The User object whose TotalLevel needs to be updated.
    :param user_category_xp_dict: Dictionary of user's category XP entries before level-up.
    """
    # Sum all category levels before the level-up
    total_category_levels_before = sum(ucxp.CategoryLevel for ucxp in user_category_xp_dict.values())
    
    # Since one category level is increasing, total category levels will increase by 1
    total_category_levels_after = total_category_levels_before + 1
    
    # Increase TotalLevel by 1 on top of the total of all categories
    user.TotalLevel = total_category_levels_after + 1

# def run_repeating_tools():
#     while True:
#         process_repeating_tools()
#         time.sleep(5)  # Wait for 5 seconds

# if __name__ == "__main__":
#     run_repeating_tools()