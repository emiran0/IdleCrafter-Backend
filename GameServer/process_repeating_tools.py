# process_repeating_tools.py

import time
from Database.database import SessionLocal
from Database.models import UserTool, Tool, ToolGeneratableItem, Item, UserItem, User
from sqlalchemy.orm import joinedload
import random

def process_repeating_tools():
    db = SessionLocal()
    try:
        user_tools = db.query(UserTool).join(Tool).options(
            # Update the relationship to 'generated_item'
            joinedload(UserTool.tool).joinedload(Tool.generatable_items).joinedload(ToolGeneratableItem.generated_item),
            # Ensure user and user's items are loaded
            joinedload(UserTool.user).joinedload(User.items),
            # Remove redundant joinedload(UserTool.tool)
        ).filter(
            Tool.isRepeating == True,
            UserTool.isEnabled == True
        ).all()

        # Get the total number of unique users
        unique_users = {user_tool.user.Id for user_tool in user_tools}
        total_users = len(unique_users)

        print(f"Processing {len(user_tools)} repeating tools for {total_users} unique users.")
        
        for user_tool in user_tools:
            user = user_tool.user
            tool = user_tool.tool

            # Get the user's item quantities
            user_items_dict = {ui.UniqueName: ui for ui in user.items}

            # Check for storage capacity
            storage_capacity = tool.StorageCapacity

            for gen_item_assoc in tool.generatable_items:
                item = gen_item_assoc.generated_item  # Updated attribute access
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
                    print(f"Deducted {resource_quantity} x '{resource_unique_name}' from user '{user.Username}'.")

                # Probability check
                probability = (item.Probability or 1.0) * (tool.ProbabilityBoost or 1.0)
                if random.random() <= probability:
                    user_item = user_items_dict.get(item.UniqueName)
                    current_quantity = user_item.Quantity if user_item else 0

                    # Check storage capacity
                    if storage_capacity is not None and current_quantity >= storage_capacity:
                        print(f"Storage capacity reached for '{item.Name}' for user '{user.Username}'.")
                        continue  # Skip adding item

                    # Calculate how many items can be added without exceeding storage capacity
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

            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error processing repeating tools: {e}")
    finally:
        db.close()

# def run_repeating_tools():
#     while True:
#         process_repeating_tools()
#         time.sleep(5)  # Wait for 5 seconds

# if __name__ == "__main__":
#     run_repeating_tools()