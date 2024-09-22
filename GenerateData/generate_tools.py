# generate_tools.py

import csv
from Database.database import SessionLocal
from Database.models import Tool
from sqlalchemy.exc import IntegrityError

def create_tool(tool_data):
    db = SessionLocal()
    try:
        # Parse boolean fields
        is_repeating = tool_data.get('isRepeating', '').strip().lower() == 'true'

        # Parse float fields
        probability_boost = float(tool_data['ProbabilityBoost']) if tool_data.get('ProbabilityBoost') else 1.0

        # Parse integer fields
        storage_capacity = int(tool_data['StorageCapacity']) if tool_data.get('StorageCapacity') else None

        # Create the Tool object
        new_tool = Tool(
            UniqueName=tool_data['UniqueName'],
            Name=tool_data['Name'],
            Category=tool_data['Category'],
            isRepeating=is_repeating,
            ProbabilityBoost=probability_boost,
            ToolDescription=tool_data.get('ToolDescription'),
            StorageCapacity=storage_capacity
        )

        db.add(new_tool)
        db.commit()
        db.refresh(new_tool)
        print(f"Tool '{new_tool.Name}' created with ID: {new_tool.Id}")

    except IntegrityError as e:
        db.rollback()
        print(f"Integrity Error: {e.orig}")
    except Exception as e:
        db.rollback()
        print(f"Error creating tool: {e}")
    finally:
        db.close()

def create_tools_from_csv(csv_filename):
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                create_tool(row)
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file '{csv_filename}': {e}")

if __name__ == "__main__":
    csv_file_path = 'GameData/ToolData.csv'  # Adjust the path if necessary
    create_tools_from_csv(csv_file_path)