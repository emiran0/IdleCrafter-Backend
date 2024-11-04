# API/api_db_access.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import NoResultFound
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import uuid
from Database.database import AsyncSessionLocal
from Database.models import (
    User, UserTool, Tool, UserItem, Item, ToolCraftingRecipe, CraftingRecipe, Market, MarketHistory, ChatHistory
)
from .api_response_models import CraftableTool, RequiredItem, ToolRecipes, Recipe, InputItem, MarketListing, TransactionHistoryResponse
from collections import Counter



# Function to get user tools
async def fetch_user_tools(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserTool)
            .options(
                selectinload(UserTool.tool)
            )
            .filter(UserTool.UserId == user_id)
        )
        user_tools = result.scalars().all()
    return user_tools

# Function to get user items
async def fetch_user_items(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserItem)
            .options(
                selectinload(UserItem.item)
            )
            .filter(UserItem.UserId == user_id)
        )
        user_items = result.scalars().all()
    return user_items

# Function to get user by username
async def get_user_by_username(username):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).filter(User.Username == username)
        )
        user = result.scalar_one_or_none()
    return user

# Function to toggle the isEnabled status of a user's tool
async def toggle_user_tool_enabled(user_id: str, tool_unique_name: str) -> UserTool:
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the UserTool for the user and tool_unique_name
            result = await session.execute(
                select(UserTool)
                .filter(
                    UserTool.UserId == user_id,
                    UserTool.ToolUniqueName == tool_unique_name
                )
            )
            user_tool = result.scalar_one_or_none()
            
            if not user_tool:
                raise NoResultFound("Tool not found for user")
            
            # Toggle the isEnabled field
            user_tool.isEnabled = not user_tool.isEnabled
            
            # Save changes
            await session.commit()
            await session.refresh(user_tool)
            
            return user_tool
        except Exception as e:
            await session.rollback()
            raise e  # Re-raise exception to be handled by calling function
        
async def get_available_tool_crafting_recipes(user_identifier: str) -> List[CraftableTool]:
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the user and their tools
            user_query = select(User).where(User.Username == user_identifier).options(
                selectinload(User.tools)
            )
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            if not user:
                raise Exception(f"User '{user_identifier}' not found.")

            # Build a mapping from (ToolUniqueName, Tier) to count
            tool_counter = Counter((user_tool.ToolUniqueName, user_tool.Tier) for user_tool in user.tools)

            # Fetch all unique OutputToolUniqueNames from ToolCraftingRecipe
            all_tools_query = select(ToolCraftingRecipe.OutputToolUniqueName).distinct()
            all_tools_result = await session.execute(all_tools_query)
            all_tool_unique_names = [row[0] for row in all_tools_result.fetchall()]

            response = []

            for tool_unique_name in all_tool_unique_names:
                # Fetch all available tiers for this tool
                tiers_query = select(ToolCraftingRecipe.OutputToolTier).where(
                    ToolCraftingRecipe.OutputToolUniqueName == tool_unique_name
                ).distinct()
                tiers_result = await session.execute(tiers_query)
                available_tiers = sorted([row[0] for row in tiers_result.fetchall()])

                # Fetch all Tool entries for this tool_unique_name
                tool_entries_query = select(Tool).where(
                    Tool.UniqueName == tool_unique_name
                )
                tool_entries_result = await session.execute(tool_entries_query)
                tool_entries = tool_entries_result.scalars().all()

                # Build a mapping of tier to Tool object
                tier_to_tool = {tool.Tier: tool for tool in tool_entries}

                # Build a mapping of tier to user's count at that tier
                user_tool_counts = {tier: count for ((name, tier), count) in tool_counter.items() if name == tool_unique_name}

                # Iterate over available tiers
                next_tier = None
                for tier in available_tiers:
                    tool = tier_to_tool.get(tier)
                    if not tool:
                        continue  # Tool not found, skip

                    is_multiple_craftable = tool.isMultipleCraftable
                    max_crafting_number = tool.maxCraftingNumber

                    user_count_at_tier = user_tool_counts.get(tier, 0)

                    if is_multiple_craftable:
                        if user_count_at_tier < max_crafting_number:
                            # User can craft more at this tier
                            next_tier = tier
                            break  # Found the next tier to craft
                        else:
                            # User has reached max crafting number at this tier, check next tier
                            continue
                    else:
                        if user_count_at_tier == 0:
                            # User doesn't have this tool at this tier
                            next_tier = tier
                            break  # Found the next tier to craft
                        else:
                            # User has the tool at this tier, check next tier
                            continue

                if next_tier is None:
                    # No tiers left to consider for this tool
                    continue  # Skip to next tool

                # Fetch required items for this tool at next_tier
                required_items_query = select(ToolCraftingRecipe).where(
                    ToolCraftingRecipe.OutputToolUniqueName == tool_unique_name,
                    ToolCraftingRecipe.OutputToolTier == next_tier
                ).options(
                    selectinload(ToolCraftingRecipe.input_item)
                )
                required_items_result = await session.execute(required_items_query)
                required_recipes = required_items_result.scalars().all()

                required_items_list = []
                for recipe in required_recipes:
                    input_item = recipe.input_item
                    if not input_item:
                        continue  # Input item not found, skip

                    required_items_list.append(RequiredItem(
                        item_unique_name=recipe.InputItemUniqueName,
                        item_display_name=input_item.Name,
                        required_quantity=recipe.InputQuantity
                    ))

                # Create the CraftableTool object including the tier
                response.append(CraftableTool(
                    unique_tool_name=tool_unique_name,
                    display_name=tool.Name,
                    tier=next_tier,
                    required_items=required_items_list
                ))

            # Sort the response by tier in ascending order
            response.sort(key=lambda x: x.tier)

            return response

        except Exception as e:
            print(f"Error fetching tool crafting recipes: {e}")
            raise

# Function to get item crafting recipes
async def get_item_crafting_recipes() -> List[ToolRecipes]:
    async with AsyncSessionLocal() as session:
        try:
            # Fetch all CraftingRecipes with related Tool, OutputItem, and InputItem
            recipes_query = select(CraftingRecipe).options(
                joinedload(CraftingRecipe.tool),
                joinedload(CraftingRecipe.output_item),
                joinedload(CraftingRecipe.input_item)
            )
            recipes_result = await session.execute(recipes_query)
            crafting_recipes = recipes_result.scalars().all()

            # Organize data into a nested dictionary
            tool_recipes_dict: Dict[tuple, Dict[str, any]] = {}

            for crafting_recipe in crafting_recipes:
                tool_key = (crafting_recipe.ToolUniqueName, crafting_recipe.ToolTier)
                output_item_key = crafting_recipe.OutputItemUniqueName

                # Initialize tool entry if not exists
                if tool_key not in tool_recipes_dict:
                    tool = crafting_recipe.tool
                    tool_recipes_dict[tool_key] = {
                        "unique_tool_name": tool.UniqueName,
                        "tool_tier": tool.Tier,
                        "recipe_dict": {}
                    }

                tool_entry = tool_recipes_dict[tool_key]

                # Initialize recipe entry if not exists
                if output_item_key not in tool_entry["recipe_dict"]:
                    output_item = crafting_recipe.output_item
                    tool_entry["recipe_dict"][output_item_key] = {
                        "output_item_unique_name": output_item.UniqueName,
                        "output_item_display_name": output_item.Name,
                        "generation_duration": int(crafting_recipe.GenerationDuration),
                        "input_items": []
                    }

                recipe_entry = tool_entry["recipe_dict"][output_item_key]

                # Add input item to the recipe's input items
                input_item = crafting_recipe.input_item
                recipe_entry["input_items"].append(InputItem(
                    input_item_unique_name=input_item.UniqueName,
                    input_item_display_name=input_item.Name,
                    input_item_quantity=crafting_recipe.InputQuantity
                ))

            # Convert the nested dictionary to the response format
            response = []
            for tool_info in tool_recipes_dict.values():
                recipe_list = []
                for recipe_info in tool_info["recipe_dict"].values():
                    recipe_list.append(Recipe(
                        output_item_unique_name=recipe_info["output_item_unique_name"],
                        output_item_display_name=recipe_info["output_item_display_name"],
                        generation_duration=recipe_info["generation_duration"],
                        input_items=recipe_info["input_items"]
                    ))
                response.append(ToolRecipes(
                    unique_tool_name=tool_info["unique_tool_name"],
                    tool_tier=tool_info["tool_tier"],
                    recipe_list=recipe_list
                ))

            return response

        except Exception as e:
            print(f"Error fetching item crafting recipes: {e}")
            raise

# Function to get market listings
async def fetch_market_listings() -> List[MarketListing]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Market)
            .options(
                selectinload(Market.item),
                selectinload(Market.seller)
            )
            .order_by(Market.ListCreatedAt.desc())
        )
        listings = result.scalars().all()
        market_listings = []
        for listing in listings:
            if listing.ExpireDate < datetime.now():
                await cancel_market_listing(listing.Id, listing.SellerId)
            else:
                market_listings.append(MarketListing(
                    id=listing.Id,
                    seller_id=str(listing.SellerId),
                    seller_username=listing.SellerUsername,
                    item_unique_name=listing.ItemUniqueName,
                    item_display_name=listing.item.Name,
                    item_description=listing.item.ItemDescription,
                    quantity=listing.Quantity,
                    price=listing.Price,
                    list_created_at=listing.ListCreatedAt,
                    expire_date=listing.ExpireDate
                ))
            
        return market_listings

# Function to create a market listing
async def create_market_listing(user: User, item_unique_name: str, quantity: int, price: float, expire_date: Optional[datetime]=None):
    async with AsyncSessionLocal() as session:
        try:
            # Check if user has enough of the item
            user_item_query = select(UserItem).filter(
                UserItem.UserId == user.Id,
                UserItem.UniqueName == item_unique_name
            )
            result = await session.execute(user_item_query)
            user_item = result.scalar_one_or_none()
            if not user_item or user_item.Quantity < quantity:
                raise Exception("Insufficient quantity of item to list.")
            # Deduct the quantity from the user's inventory
            user_item.Quantity -= quantity
            session.add(user_item)
            # Create the market listing
            new_listing = Market(
                SellerId=user.Id,
                SellerUsername=user.Username,
                ItemUniqueName=item_unique_name,
                Quantity=quantity,
                Price=price,
                ListCreatedAt=datetime.now(),
                ExpireDate=datetime.now() + timedelta(days=3)
            )
            session.add(new_listing)
            await session.commit()
            await session.refresh(new_listing)
            return new_listing
        except Exception as e:
            await session.rollback()
            raise e

# Function to buy items from the market
async def buy_market_item(buyer: User, listing_id: int, quantity: int):
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the listing
            listing_query = select(Market).filter(
                Market.Id == listing_id
            ).options(
                selectinload(Market.item),
                selectinload(Market.seller)
            )
            result = await session.execute(listing_query)
            listing = result.scalar_one_or_none()
            if not listing:
                raise Exception("Listing not found.")
            if listing.Quantity < quantity:
                raise Exception("Not enough quantity available in the listing.")
            if listing.SellerId == buyer.Id:
                raise Exception("Cannot buy your own listing.")
            # Calculate total price
            total_price = listing.Price * quantity
            if buyer.Gold < total_price:
                raise Exception("Insufficient gold to complete the purchase.")
            # Deduct gold from buyer
            buyer.Gold -= total_price
            session.add(buyer)
            # Add gold to seller
            seller_query = select(User).filter(User.Id == listing.SellerId)
            seller_result = await session.execute(seller_query)
            seller = seller_result.scalar_one_or_none()
            if seller:
                seller.Gold += total_price
                session.add(seller)
            # Add item to buyer's inventory
            buyer_item_query = select(UserItem).filter(
                UserItem.UserId == buyer.Id,
                UserItem.UniqueName == listing.ItemUniqueName
            )
            buyer_item_result = await session.execute(buyer_item_query)
            buyer_item = buyer_item_result.scalar_one_or_none()
            if buyer_item:
                buyer_item.Quantity += quantity
            else:
                buyer_item = UserItem(
                    UserId=buyer.Id,
                    Username=buyer.Username,
                    UniqueName=listing.ItemUniqueName,
                    Quantity=quantity
                )
                session.add(buyer_item)

            # Save the transaction to market history
            await save_market_transaction(
                buyer_id=buyer.Id,
                seller_id=listing.SellerId,
                buyer_username=buyer.Username, 
                seller_username=listing.SellerUsername, 
                item_unique_name=listing.ItemUniqueName, 
                quantity=quantity, price=total_price
                )
            
            # Deduct quantity from listing
            listing.Quantity -= quantity
            if listing.Quantity == 0:
                await session.delete(listing)
            else:
                session.add(listing)
            await session.commit()
            await session.refresh(buyer)  # Refresh buyer to get updated Gold
            return {
                'total_price': total_price,
                'item_unique_name': listing.ItemUniqueName,
                'item_display_name': listing.item.Name,
                'quantity_bought': quantity,
                'buyer_gold_balance': buyer.Gold
            }
        except Exception as e:
            await session.rollback()
            raise e
        
# Function to save the transaction to market history
async def save_market_transaction(
        buyer_id: str, seller_id: str, buyer_username: str, 
        seller_username : str, item_unique_name: str,
        quantity: int, price: float
        ):
    async with AsyncSessionLocal() as session:
        try:
            new_transaction = MarketHistory(
                BuyerId=buyer_id,
                BuyerUsername=buyer_username,
                SellerId=seller_id,
                SellerUsername=seller_username,
                ItemUniqueName=item_unique_name,
                Quantity=quantity,
                Price=price,
                BuyingDate=datetime.now()
            )
            session.add(new_transaction)
            await session.commit()
            await session.refresh(new_transaction)
            return new_transaction
        except Exception as e:
            await session.rollback()
            raise e
        
# Function to get transaction history
async def get_transaction_history(
    start_date: datetime,
    end_date: datetime,
    item_unique_name: str
) -> List[MarketHistory]:
    async with AsyncSessionLocal() as session:
        try:
            query = select(MarketHistory).filter(
                    MarketHistory.BuyingDate >= start_date,
                    MarketHistory.BuyingDate <= end_date,
                    MarketHistory.ItemUniqueName == item_unique_name
            ).order_by(MarketHistory.BuyingDate)

            result = await session.execute(query)
            transactions = result.scalars().all()
            return transactions

        except Exception as e:
            print(f"Error fetching transaction history: {e}")
            raise e
        
# Function to see user's active market listings
async def fetch_user_market_listings(ListCreator: User) -> List[MarketListing]:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Market)
                .options(
                    selectinload(Market.item)
                )
                .filter(Market.SellerId == ListCreator.Id)
                .order_by(Market.ListCreatedAt.desc())
            )
            listings = result.scalars().all()

            if not listings:
                raise Exception("No active listings found.")
            
            market_listings = []
            for listing in listings:

                if listing.ExpireDate < datetime.now():
                    await cancel_market_listing(listing.Id, ListCreator.Id)

                market_listings.append(MarketListing(
                    id=listing.Id,
                    seller_id=str(listing.SellerId),
                    seller_username=listing.SellerUsername,
                    item_unique_name=listing.ItemUniqueName,
                    item_display_name=listing.item.Name,
                    item_description=listing.item.ItemDescription,
                    quantity=listing.Quantity,
                    price=listing.Price,
                    list_created_at=listing.ListCreatedAt,
                    expire_date=listing.ExpireDate
                ))
                
            return market_listings
        
        except Exception as e:
            await session.rollback()
            raise e
    
# Function to cancel a market listing
async def cancel_market_listing(listing_id : int, seller_id : str):
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the listing
            listing_query = select(Market).filter(
                Market.Id == listing_id
            )
            result = await session.execute(listing_query)
            listing = result.scalar_one_or_none()

            if not listing:
                raise Exception("Listing not found.")
            if listing.SellerId != seller_id:
                raise Exception("Unauthorized to cancel this listing.")
            
            # Return the quantity to the seller's inventory
            seller_item_query = select(UserItem).filter(
                UserItem.UserId == listing.SellerId,
                UserItem.UniqueName == listing.ItemUniqueName
                )
            seller_item_result = await session.execute(seller_item_query)
            seller_item = seller_item_result.scalar_one_or_none()

            if seller_item:
                seller_item.Quantity += listing.Quantity

            else:
                seller_item = UserItem(
                    UserId=listing.SellerId,
                    Username=listing.SellerUsername,
                    UniqueName=listing.ItemUniqueName,
                    Quantity=listing.Quantity
                )
                session.add(seller_item)

            # Delete the listing
            await session.delete(listing)
            await session.commit()
            return True
        
        except Exception as e:
            await session.rollback()
            raise e
        
# Function to quick-sell an item for the user
async def quick_sell_user_item(user: User, item_unique_name: str, quantity: int):
    async with AsyncSessionLocal() as session:
        try:
            # Fetch the user item
            print(item_unique_name)
            print(user.Id)
            print(quantity)
            user_item_query = select(UserItem).where(
                UserItem.UserId == user.Id,
                UserItem.UniqueName == item_unique_name
            )
            result = await session.execute(user_item_query)
            user_item = result.scalar_one_or_none()
            if not user_item or user_item.Quantity < quantity:
                raise Exception("Insufficient quantity of item to sell.")
            # Fetch the item's sell price
            item_query = select(Item).filter(Item.UniqueName == item_unique_name)
            item_result = await session.execute(item_query)
            item = item_result.scalar_one_or_none()
            if not item:
                raise Exception("Item not found.")
            total_price = item.GoldValue * quantity
            # Deduct the quantity from the user's inventory
            user_item.Quantity -= quantity
            session.add(user_item)
            # Add gold to the user
            user.Gold += total_price
            session.add(user)
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
            raise e
        
# Function to save chat message from user         
async def save_chat_message(user_id: uuid.UUID, username: str, message_text: str) -> ChatHistory:
    async with AsyncSessionLocal() as session:
        chat_message = ChatHistory(
            UserId=user_id,
            Username=username,
            Text=message_text,
            Time=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)
        return chat_message