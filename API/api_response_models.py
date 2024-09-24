# API/api_response_models.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict

# Request model for user signup
class SignupRequest(BaseModel):
    """Model for user signup request"""
    Username: str
    Email: EmailStr
    Password: str

# User model for response
class UserResponse(BaseModel):
    Username: str
    Email: str
    Gold: float
    Energy: float

    class Config:
        from_attributes = True

# Token response model
class Token(BaseModel):
    access_token: str
    token_type: str

# Request model for crafting a tool
class CraftToolRequest(BaseModel):
    tool_unique_name: str

# Request model for crafting an item
class CraftItemRequest(BaseModel):
    item_unique_name: str
    quantity: int = 1  # Default quantity to 1

# Model for tool data 
class ToolData(BaseModel):
    unique_tool_name: str
    display_name: str
    isRepeating: Optional[bool]
    isEnabled: Optional[bool]
    isOccupied: Optional[bool]
    Tier: Optional[int]
    LastUsed: Optional[datetime]
    ongoingCraftingItemUniqueName: Optional[str]
    OngoingRemainedQuantity: Optional[int]

# Response model for user's tools
class UserToolsResponse(BaseModel):
    tools_by_category: Dict[str, List[ToolData]]

# Model for item data 
class ItemData(BaseModel):
    item_unique_name: str
    item_quantity: int
    item_display_name: str

# Response model for user's items
class UserItemsResponse(BaseModel):
    items_by_category: Dict[str, List[ItemData]]

# Response model for toggling a tool
class ToolToggleResponse(BaseModel):
    tool_unique_name: str
    isEnabled: bool