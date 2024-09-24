from .generate_items import main_create_items
from .generate_tools import main_create_tools
from .generate_tool_generatables import main_tool_generatable_items
from .generate_tool_crafting_recipes import main_tool_crafting_recipes
from .generate_crafting_recipes import main_crafting_recipes

def main_generate_all_game_data():
    main_create_items()
    main_create_tools()
    main_tool_generatable_items()
    main_tool_crafting_recipes()
    main_crafting_recipes()
    print("All pre-game data generated.")

if __name__ == '__main__':
    main_generate_all_game_data()
