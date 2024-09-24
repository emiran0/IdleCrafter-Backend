# API/api_app.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .auth import authenticate_user, create_access_token, get_current_user
from datetime import timedelta
from pydantic import BaseModel, EmailStr
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError

from GameServer.process_repeating_tools import process_repeating_tools
from GameServer.crafting_ongoing_process import crafting_ongoing_process
from GameServer.craft_tool_process import craft_tool
from GameServer.craft_process import craft_item
from GenerateData.create_users import create_user


# Background task functions
async def run_process_repeating_tools():
    while True:
        await asyncio.to_thread(process_repeating_tools)
        await asyncio.sleep(5)

async def run_crafting_ongoing_process():
    while True:
        await crafting_ongoing_process()
        await asyncio.sleep(5)

# Background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
# Start background tasks
    task1 = asyncio.create_task(run_process_repeating_tools())
    task2 = asyncio.create_task(run_crafting_ongoing_process())
    yield
    task1.cancel()
    task2.cancel()
    await asyncio.gather(task1, task2, return_exceptions=True)

# Create the FastAPI app
app = FastAPI(lifespan=lifespan)

# Request model for user signup
class SignupRequest(BaseModel):
    Username: str
    Email: EmailStr
    Password: str
    
# User model for response
class UserResponse(BaseModel):
    Username: str
    Email: str
    Gold: int
    Energy: int

    class Config:
        orm_mode = True

# Token response model
class Token(BaseModel):
    access_token: str
    token_type: str

class CraftToolRequest(BaseModel):
    tool_unique_name: str

class CraftItemRequest(BaseModel):
    item_unique_name: str
    quantity: int = 1  # Default quantity to 1

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
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.Username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route example
@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.post("/signup")
async def signup(request: SignupRequest):
    try:
        # Convert the request data to a dictionary
        user_data = request.model_dump()
        print(user_data)
        
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
    except IntegrityError:
        # Handle duplicate username or email
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to craft a tool
@app.post("/craft/tool")
async def craft_tool_endpoint(
    request: CraftToolRequest,
    current_user: UserResponse = Depends(get_current_user)
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
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        # Call the async function to craft the item
        result = await craft_item(current_user.Username, request.item_unique_name, request.quantity)
        return result  # Return the dictionary directly
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail=str(e))

