# generate_items.py

import csv
from Database.database import SessionLocal
from Database.models import Item
from sqlalchemy.exc import IntegrityError

def create_item(item_data):
    db = SessionLocal()
    try:
        # Create the Item object
        new_item = Item(
            UniqueName=item_data['UniqueName'],
            Name=item_data['Name'],
            Category=item_data['Category'],
            GoldValue=float(item_data['GoldValue']) if item_data.get('GoldValue') else None,
            Probability=float(item_data['Probability']) if item_data.get('Probability') else None,
            isLegendary=item_data.get('isLegendary', '').strip().lower() == 'true',
            isCraftable=item_data.get('isCraftable', '').strip().lower() == 'true',
            ItemDescription=item_data.get('ItemDescription')
        )

        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        print(f"Item '{new_item.Name}' created with ID: {new_item.Id}")

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

if __name__ == "__main__":
    csv_file_path = 'GameData/ItemData.csv'  # Adjust the path if necessary
    create_items_from_csv(csv_file_path)