# API/api_app.py

from fastapi import FastAPI, Depends, HTTPException, status, Path, Query
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, get_current_user
from datetime import timedelta, datetime
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError, NoResultFound
from collections import OrderedDict
from typing import List

from .api_response_models import (
    SignupRequest, UserResponse, Token,
    CraftToolRequest, CraftItemRequest,
    ToolData, ItemData, UserToolsResponse, UserItemsResponse,
    ToolToggleResponse, CraftableTool, RequiredItem, ToolRecipes,
    MarketListingsResponse, ListItemRequest, ListItemResponse,
    BuyItemRequest, BuyItemResponse, CancelListingResponse, CancelListingRequest,
    ItemQuickSellRequest, TransactionHistoryResponse, TransactionHistoryItem
)
from .api_db_access import (
    fetch_user_tools, fetch_user_items, get_user_by_username, toggle_user_tool_enabled,
    get_available_tool_crafting_recipes, get_item_crafting_recipes, fetch_market_listings, 
    create_market_listing, buy_market_item, cancel_market_listing, fetch_user_market_listings,
    quick_sell_user_item, get_transaction_history
)
from GenerateData.create_users import create_user, UserAlreadyExistsError
from GameServer.process_repeating_tools import process_repeating_tools
from GameServer.crafting_ongoing_process import crafting_ongoing_process
from GameServer.craft_tool_process import craft_tool
from GameServer.craft_process import craft_item
from Database.models import User

# Background task functions
async def run_process_repeating_tools():
    while True:
        await asyncio.to_thread(process_repeating_tools)
        await asyncio.sleep(5)

async def run_crafting_ongoing_process():
    while True:
        await crafting_ongoing_process()
        await asyncio.sleep(5)

# Lifespan function to manage startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background tasks
    task1 = asyncio.create_task(run_process_repeating_tools())
    task2 = asyncio.create_task(run_crafting_ongoing_process())
    yield
    # Cancel tasks on shutdown
    task1.cancel()
    task2.cancel()
    await asyncio.gather(task1, task2, return_exceptions=True)

# Create the FastAPI app
app = FastAPI(lifespan=lifespan, title="IdleCrafter API", version="1", description="API created for IdleCrafter game")

# Route to obtain JWT token
@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.Username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route example
@app.get("/users/me", response_model=UserResponse, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Signup endpoint
@app.post("/signup", response_model=Token, tags=["Authentication"])
async def signup(request: SignupRequest):
    try:
        # Convert the request data to a dictionary
        user_data = request.model_dump()
        
        # Call the existing create_user function
        new_user = await create_user(user_data)
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": new_user.Username}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "Username": new_user.Username,
                "Email": new_user.Email
            }
        }
    except UserAlreadyExistsError as e:
        # Handle duplicate username or email
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Handle other integrity errors
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to craft a tool
@app.post("/craft/tool", tags=["Crafting"])
async def craft_tool_endpoint(
    request: CraftToolRequest,
    current_user: User = Depends(get_current_user)
):
    result = await craft_tool(current_user.Username, request.tool_unique_name, request.tool_tier)
    return result  # Return the success message
    
# Endpoint to craft an item
@app.post("/craft/item", tags=["Crafting"])
async def craft_item_endpoint(
    request: CraftItemRequest,
    current_user: User = Depends(get_current_user)
):
    # Call the async function to craft the item
    result = await craft_item(current_user.Username, request.item_unique_name, request.quantity)
    return result  # Return the success message

# GET endpoint for user's tools
@app.get("/user/tools", response_model=UserToolsResponse, tags=["Tools"])
async def get_user_tools(current_user: User = Depends(get_current_user)):
    try:
        user_tools = await fetch_user_tools(current_user.Id)
        tools_by_category = {}

        for user_tool in user_tools:
            tool = user_tool.tool

            category = tool.Category

            tool_data = ToolData(
                unique_tool_name=tool.UniqueName,
                display_name=tool.Name,
                isRepeating=tool.isRepeating,
                isEnabled=user_tool.isEnabled,
                isOccupied=user_tool.isOccupied,
                Tier=user_tool.Tier,
                LastUsed=user_tool.LastUsed,
                ongoingCraftingItemUniqueName=user_tool.OngoingCraftingItemUniqueName,
                OngoingRemainedQuantity=user_tool.OngoingRemainedQuantity
            )

            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool_data)

        # Sort tools within each category by display_name
        for category in tools_by_category:
            tools_by_category[category].sort(key=lambda x: x.display_name)

        # Sort categories alphabetically
        sorted_tools_by_category = OrderedDict(sorted(tools_by_category.items()))

        return UserToolsResponse(tools_by_category=sorted_tools_by_category)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET endpoint for user's items
@app.get("/user/items", response_model=UserItemsResponse, tags=["Items"])
async def get_user_items(current_user: User = Depends(get_current_user)):
    try:
        user_items = await fetch_user_items(current_user.Id)
        items_by_category = {}

        for user_item in user_items:
            item = user_item.item

            category = item.Category

            item_data = ItemData(
                item_unique_name=item.UniqueName,
                item_quantity=user_item.Quantity,
                item_display_name=item.Name,
                item_gold_value=item.GoldValue
            )

            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item_data)

        # Sort items within each category by item_display_name
        for category in items_by_category:
            items_by_category[category].sort(key=lambda x: x.item_display_name)

        # Sort categories alphabetically
        sorted_items_by_category = OrderedDict(sorted(items_by_category.items()))

        return UserItemsResponse(items_by_category=sorted_items_by_category)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/user/items/quick-sell", tags=["Items"])
async def quick_sell_item(
    request: ItemQuickSellRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Call the database access function to quick sell the item
        await quick_sell_user_item(current_user, request.item_unique_name, request.item_quantity)
        return {"status": "success", "message": f"Item {request.item_unique_name} quick-sold."}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found for user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PATCH endpoint to toggle tool enabled status    
@app.patch("/user/tools/{tool_unique_name}/toggle", response_model=ToolToggleResponse, tags=["Tools"])
async def toggle_tool_enabled(
    tool_unique_name: str = Path(..., description="Unique name of the tool"),
    current_user: User = Depends(get_current_user)
):
    try:
        # Call the database access function to toggle the tool's isEnabled status
        user_tool = await toggle_user_tool_enabled(current_user.Id, tool_unique_name)
        
        # Prepare response
        response = ToolToggleResponse(
            tool_unique_name=tool_unique_name,
            isEnabled=user_tool.isEnabled
        )
        return response
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Tool not found for user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# GET endpoint to fetch tool crafting recipes    
@app.get("/tool-crafting-recipes", response_model=List[CraftableTool], tags=["Crafting"])
async def get_tool_crafting_recipes(current_user: User = Depends(get_current_user)):
    try:
        recipes = await get_available_tool_crafting_recipes(current_user.Username)
        return recipes
    except Exception as e:
        print(f"Error fetching tool crafting recipes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# GET endpoint to fetch item crafting recipes
@app.get("/item-crafting-recipes", response_model=List[ToolRecipes], tags=["Crafting"])
async def get_item_crafting_recipes_endpoint(current_user: User = Depends(get_current_user)):
    try:
        recipes = await get_item_crafting_recipes()
        return recipes
    except Exception as e:
        print(f"Error fetching item crafting recipes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# New endpoint to get market listings
@app.get("/market/listings", response_model=MarketListingsResponse, tags=["Market"])
async def get_market_listings(current_user: User = Depends(get_current_user)):
    try:
        listings = await fetch_market_listings()
        return MarketListingsResponse(listings=listings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to list an item for selling
@app.post("/market/list", response_model=ListItemResponse, tags=["Market"])
async def list_item_for_sale(
    request: ListItemRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        new_listing = await create_market_listing(
            user=current_user,
            item_unique_name=request.item_unique_name,
            quantity=request.quantity,
            price=request.price,
            expire_date=request.expire_date
        )
        return ListItemResponse(
            status="success",
            message="Item listed for sale.",
            listing_id=new_listing.Id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# New endpoint to buy items from the market
@app.post("/market/buy", response_model=BuyItemResponse, tags=["Market"])
async def buy_market_item_endpoint(
    request: BuyItemRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        purchase_details = await buy_market_item(
            buyer=current_user,
            listing_id=request.listing_id,
            quantity=request.quantity
        )
        return BuyItemResponse(
            status="success",
            message="Purchase completed.",
            total_price=purchase_details['total_price'],
            item_unique_name=purchase_details['item_unique_name'],
            item_display_name=purchase_details['item_display_name'],
            quantity_bought=purchase_details['quantity_bought'],
            buyer_gold_balance=purchase_details['buyer_gold_balance']
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# New endpoint to list user's active market listings
@app.get("/market/my-listings", response_model=MarketListingsResponse, tags=["Market"])
async def get_user_market_listings(current_user: User = Depends(get_current_user)):
    try:
        listings = await fetch_user_market_listings(ListCreator=current_user)
        return MarketListingsResponse(listings=listings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
# New endpoint to cancel a market listing
@app.delete("/market/my-listings/cancel", tags=["Market"], response_model=CancelListingResponse)
async def cancel_user_market_listing(
    request: CancelListingRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        await cancel_market_listing(
            seller_id=current_user.Id,
            listing_id=request.listing_id
        )
        return CancelListingResponse(status="success", message=f"Listing {request.listing_id} cancelled.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/market/transactions", response_model=TransactionHistoryResponse, tags=["Market"])
async def get_transaction_history_endpoint(
    start_date: datetime = Query(..., description="Start date in ISO format"),
    end_date: datetime = Query(..., description="End date in ISO format"),
    item_unique_name: str = Query(..., description="Unique name of the item"),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate that start_date is not after end_date
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
        
        # Fetch transaction history
        transactions = await get_transaction_history(
            start_date=start_date,
            end_date=end_date,
            item_unique_name=item_unique_name
        )

        transaction_items = [
            TransactionHistoryItem(
                item_unique_name=tx.ItemUniqueName,
                transaction_date=tx.BuyingDate,
                quantity=tx.Quantity,
                price=tx.Price
            )
            for tx in transactions
        ]

        return TransactionHistoryResponse(transactions=transaction_items)

    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error fetching transaction history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
