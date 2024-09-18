# generate_tool_generatable_items.py

import csv
from Database.database import SessionLocal
from Database.models import ToolGeneratableItem, Tool, Item
from sqlalchemy.exc import IntegrityError

def create_tool_generatable_item(data):
    db = SessionLocal()
    try:
        # Check if Tool and Item exist
        tool = db.query(Tool).filter(Tool.UniqueName == data['ToolUniqueName']).first()
        if not tool:
            print(f"Tool '{data['ToolUniqueName']}' not found.")
            return

        item = db.query(Item).filter(Item.UniqueName == data['ItemUniqueName']).first()
        if not item:
            print(f"Item '{data['ItemUniqueName']}' not found.")
            return

        # Create the ToolGeneratableItem object
        new_tgi = ToolGeneratableItem(
            ToolUniqueName=data['ToolUniqueName'],
            ItemUniqueName=data['ItemUniqueName']
        )

        db.add(new_tgi)
        db.commit()
        db.refresh(new_tgi)
        print(f"ToolGeneratableItem created: Tool '{data['ToolUniqueName']}' can generate Item '{data['ItemUniqueName']}'.")

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating ToolGeneratableItem: {e}")
    finally:
        db.close()

def create_tool_generatable_items_from_csv(csv_filename):
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_tool_generatable_item(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

if __name__ == "__main__":
    csv_file_path = 'GameData/GeneratableItemsData.csv'  # Adjust the path if necessary
    create_tool_generatable_items_from_csv(csv_file_path)