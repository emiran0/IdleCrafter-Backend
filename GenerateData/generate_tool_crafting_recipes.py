# generate_tool_crafting_recipes.py

import csv
from Database.database import SessionLocal
from Database.models import ToolCraftingRecipe, Item, Tool
from sqlalchemy.exc import IntegrityError

def create_tool_crafting_recipe(data):
    db = SessionLocal()
    try:
        # Check if Input Item exists
        input_item = db.query(Item).filter(Item.UniqueName == data['InputItemUniqueName']).first()
        if not input_item:
            print(f"Input item '{data['InputItemUniqueName']}' not found.")
            return

        # Check if Output Tool exists
        output_tool = db.query(Tool).filter(Tool.UniqueName == data['OutputToolUniqueName']).first()
        if not output_tool:
            print(f"Output tool '{data['OutputToolUniqueName']}' not found.")
            return

        # Create the ToolCraftingRecipe object
        new_recipe = ToolCraftingRecipe(
            InputItemUniqueName=data['InputItemUniqueName'],
            InputQuantity=int(data['InputQuantity']),
            OutputToolUniqueName=data['OutputToolUniqueName'],
            GenerationDuration=float(data['GenerationDuration']) if data.get('GenerationDuration') else None
        )

        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        print(f"ToolCraftingRecipe created: {data['InputItemUniqueName']} x{data['InputQuantity']} -> {data['OutputToolUniqueName']}")

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating ToolCraftingRecipe: {e}")
    finally:
        db.close()

def create_tool_crafting_recipes_from_csv(csv_filename):
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_tool_crafting_recipe(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

def main_tool_crafting_recipes():
    csv_file_path = 'GameData/ToolCraftingRecipesData.csv'  # Adjust the path if necessary
    create_tool_crafting_recipes_from_csv(csv_file_path)