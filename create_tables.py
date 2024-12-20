# create_tables.py

from Database.database import engine, Base
import Database.models  # Ensure models are imported so they are registered
from Database.models import (Market, MarketHistory, User, UserItem, UserTool, Item, Tool,
    ToolCraftingRecipe, ToolGeneratableItem, CategoryLevels, UserCategoryXP)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def create_specific_table():
    ToolCraftingRecipe.__table__.create(bind=engine)
    print("Table created successfully.")

if __name__ == "__main__":
    # create_tables()
    create_specific_table()