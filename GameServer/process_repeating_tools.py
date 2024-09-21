
import time
from Database.database import SessionLocal
from Database.models import UserTool, Tool, ToolGeneratableItem, Item, UserItem
from sqlalchemy.orm import joinedload
import random

def process_repeating_tools():
    db = SessionLocal()
    try:
        user_tools = db.query(UserTool).join(Tool).options(
            joinedload(UserTool.tool).joinedload(Tool.generatable_items).joinedload(ToolGeneratableItem.item),
            joinedload(UserTool.user)
        ).filter(
            Tool.isRepeating == True,
            UserTool.isEnabled == True
        ).all()
        print(f"Processing {len(user_tools)} repeating tools.")
        print(user_tools)
        for user_tool in user_tools:
            user = user_tool.user
            tool = user_tool.tool

            print(f"Processing tool '{tool.Name}' for user '{user.Username}'.")

            for gen_item_assoc in tool.generatable_items:
                item = gen_item_assoc.item
                probability = (item.Probability or 1.0) * (tool.ProbabilityBoost or 1.0)
                if random.random() <= probability:
                    user_item = db.query(UserItem).filter(
                        UserItem.UserId == user.Id,
                        UserItem.UniqueName == item.UniqueName
                    ).first()

                    if user_item:
                        user_item.Quantity += 1
                    else:
                        user_item = UserItem(
                            UserId=user.Id,
                            Username=user.Username,
                            UniqueName=item.UniqueName,
                            Quantity=1
                        )
                        db.add(user_item)

                    print(f"Generated '{item.Name}' for user '{user.Username}'.")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error processing repeating tools: {e}")
    finally:
        db.close()

def run_repeating_tools():
    while True:
        process_repeating_tools()
        time.sleep(5)  # Wait for 5 seconds

if __name__ == "__main__":
    run_repeating_tools()