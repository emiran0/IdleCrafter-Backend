# API/api_app.py

from fastapi import FastAPI, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, get_current_user
from datetime import timedelta
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError, NoResultFound
from collections import OrderedDict

from .api_response_models import (
    SignupRequest, UserResponse, Token,
    CraftToolRequest, CraftItemRequest,
    ToolData, ItemData, UserToolsResponse, UserItemsResponse,
    ToolToggleResponse
)
from .api_db_access import (
    fetch_user_tools, fetch_user_items, get_user_by_username, toggle_user_tool_enabled
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
app = FastAPI(lifespan=lifespan)

# Route to obtain JWT token
@app.post("/token", response_model=Token)
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
@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Signup endpoint
@app.post("/signup", response_model=Token)
async def signup(request: SignupRequest):
    try:
        # Convert the request data to a dictionary
        user_data = request.dict()
        
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
@app.post("/craft/tool")
async def craft_tool_endpoint(
    request: CraftToolRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Call the async function to craft the tool
        result = await craft_tool(current_user.Username, request.tool_unique_name)
        return result  # Return the dictionary directly
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail=str(e))
    
# Endpoint to craft an item
@app.post("/craft/item")
async def craft_item_endpoint(
    request: CraftItemRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Call the async function to craft the item
        result = await craft_item(current_user.Username, request.item_unique_name, request.quantity)
        return result  # Return the dictionary directly
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail=str(e))

# GET endpoint for user's tools
@app.get("/user/tools", response_model=UserToolsResponse)
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
@app.get("/user/items", response_model=UserItemsResponse)
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
                item_display_name=item.Name
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
    
# PATCH endpoint to toggle tool enabled status    
@app.patch("/user/tools/{tool_unique_name}/toggle", response_model=ToolToggleResponse)
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