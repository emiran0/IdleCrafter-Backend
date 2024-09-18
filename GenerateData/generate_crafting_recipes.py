# generate_crafting_recipes.py

import csv
from Database.database import SessionLocal
from Database.models import CraftingRecipe, Item, Tool
from sqlalchemy.exc import IntegrityError

def create_crafting_recipe(data):
    db = SessionLocal()
    try:
        # Check if Input Item, Output Item, and Tool exist
        input_item = db.query(Item).filter(Item.UniqueName == data['InputItemUniqueName']).first()
        if not input_item:
            print(f"Input item '{data['InputItemUniqueName']}' not found.")
            return

        output_item = db.query(Item).filter(Item.UniqueName == data['OutputItemUniqueName']).first()
        if not output_item:
            print(f"Output item '{data['OutputItemUniqueName']}' not found.")
            return

        tool = db.query(Tool).filter(Tool.UniqueName == data['ToolUniqueName']).first()
        if not tool:
            print(f"Tool '{data['ToolUniqueName']}' not found.")
            return

        # Create the CraftingRecipe object
        new_recipe = CraftingRecipe(
            InputItemUniqueName=data['InputItemUniqueName'],
            InputQuantity=int(data['InputQuantity']),
            ToolUniqueName=data['ToolUniqueName'],
            OutputItemUniqueName=data['OutputItemUniqueName'],
            OutputQuantity=int(data['OutputQuantity']),
            GenerationDuration=float(data['GenerationDuration']) if data.get('GenerationDuration') else None
        )

        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        print(f"CraftingRecipe created: {data['InputItemUniqueName']} x{data['InputQuantity']} + {data['ToolUniqueName']} -> {data['OutputItemUniqueName']} x{data['OutputQuantity']}")

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating CraftingRecipe: {e}")
    finally:
        db.close()

def create_crafting_recipes_from_csv(csv_filename):
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_crafting_recipe(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

if __name__ == "__main__":
    csv_file_path = 'GameData/CraftingRecipesData.csv'  # Adjust the path if necessary
    create_crafting_recipes_from_csv(csv_file_path)