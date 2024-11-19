# generate_items.py

import csv
from Database.database import SessionLocal
from Database.models import CategoryLevels
from sqlalchemy.exc import IntegrityError

def create_item(level_data):
    db = SessionLocal()
    try:
        # Create the Level object
        new_level = CategoryLevels(
            Category = level_data['Category'],
            Level = int(level_data['Level']),
            StartingXp = int(level_data['StartingXp']),
        )

        db.add(new_level)
        db.commit()
        db.refresh(new_level)
        print(f"Item '{new_level.Name}' created with ID: {new_level.Id}")

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating item: {e}")
    finally:
        db.close()

def create_items_from_csv(csv_filename):
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_item(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

def main_create_items():
    csv_file_path = 'GameData/CategoryLevelData.csv'  # Adjust the path if necessary
    create_items_from_csv(csv_file_path)
    print("Levels creation complete.")

if __name__ == "__main__":
    main_create_items()