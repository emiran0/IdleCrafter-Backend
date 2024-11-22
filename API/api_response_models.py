# API/api_response_models.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict

# Request model for user signup
class SignupRequest(BaseModel):
    """
    Model for user signup request
    
    :param Username: Username of the user
    :type Username: str
    :param Email: Email of the user
    :type Email: EmailStr
    :param Password: Password of the user
    :type Password: str
    """

    Username: str
    Email: EmailStr
    Password: str

# User model for response
class UserResponse(BaseModel):
    """
    User response model used for returning user metadata.

    :param Username: Username of the user
    :type Username: str
    :param Email: Email of the user
    :type Email: str
    :param Gold: Gold balance of the user
    :type Gold: float
    :param Energy: Energy balance of the user
    :type Energy: float
    """

    Username: str
    Email: str
    Gold: float
    Energy: float
    TotalLevel: int

    class Config:
        from_attributes = True

# Token response model
class Token(BaseModel):
    access_token: str
    token_type: str

# Request model for crafting a tool
class CraftToolRequest(BaseModel):
    """
    The request body model for tool crafting.

    :param tool_unique_name: Unique name of the tool to craft
    :type tool_unique_name: str
    :param tool_tier: Tier of the tool to craft
    :type tool_tier: int
    """

    tool_unique_name: str
    tool_tier: int = 1  # Default tier to 1

# Request model for crafting an item
class CraftItemRequest(BaseModel):
    """
    The request body model for item crafting.

    :param item_unique_name: Unique name of the item to craft
    :type item_unique_name: str
    :param quantity: Quantity of the item to craft
    :type quantity: int
    """

    item_unique_name: str
    quantity: int = 1  # Default quantity to 1

# Model for tool data 
class ToolData(BaseModel):
    """
    The base information body for a tool, fully detailed with all the necessary information.

    :param unique_tool_name: Unique name of the tool
    :type unique_tool_name: str
    :param display_name: Display name of the tool
    :type display_name: str
    :param ToolId: ID of the tool
    :type ToolId: int
    :param isRepeating: If the tool is repeating
    :type isRepeating: Optional[bool]
    :param isEnabled: If the tool is enabled
    :type isEnabled: Optional[bool]
    :param isOccupied: If the tool is occupied
    :type isOccupied: Optional[bool]
    :param Tier: Tier of the tool
    :type Tier: Optional[int]
    :param LastUsed: Last used timestamp of the tool
    :type LastUsed: Optional[datetime]
    :param ongoingCraftingItemUniqueName: Unique name of the ongoing crafting item
    :type ongoingCraftingItemUniqueName: Optional[str]
    :param OngoingRemainedQuantity: Remaining quantity of the ongoing crafting item
    :type OngoingRemainedQuantity: Optional[int]
    """

    unique_tool_name: str
    display_name: str
    ToolId: int
    isRepeating: Optional[bool]
    isEnabled: Optional[bool]
    isOccupied: Optional[bool]
    Tier: Optional[int]
    LastUsed: Optional[datetime]
    ongoingCraftingItemUniqueName: Optional[str]
    OngoingRemainedQuantity: Optional[int]

# Response model for user's tools
class UserToolsResponse(BaseModel):
    """
    The response body model for user's tools, categorized by their respective categories.

    :param tools_by_category: Tools categorized by their respective categories
    :type tools_by_category: Dict[str, List[ToolData]]
    """

    tools_by_category: Dict[str, List[ToolData]]

# Model for item data 
class ItemData(BaseModel):
    """
    The information body of the main item, fully detailed with all the necessary information.

    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param item_quantity: Quantity of the item
    :type item_quantity: int
    :param item_display_name: Display name of the item
    :type item_display_name: str
    """

    item_unique_name: str
    item_quantity: int
    item_display_name: str
    item_gold_value: float

class ItemQuickSellRequest(BaseModel):
    """
    The request information body of the main item, with only the necessary information for quick sell.

    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param item_quantity: Quantity of the item
    :type item_quantity: int
    """

    item_unique_name: str
    item_quantity: int

# Response model for user's items
class UserItemsResponse(BaseModel):
    """
    The response body model for user's items, categorized by their respective categories.

    :param items_by_category: Items categorized by their respective categories
    :type items_by_category: Dict[str, List[ItemData]]
    """

    items_by_category: Dict[str, List[ItemData]]

# Response model for toggling a tool
class ToolToggleResponse(BaseModel):
    """
    The response body model for toggling a tool.
    
    :param tool_unique_name: Unique name of the tool
    :type tool_unique_name: str
    :param isEnabled: If the tool is enabled
    :type isEnabled: bool
    """

    tool_unique_name: str
    isEnabled: bool

class RequiredItem(BaseModel):
    """
    Model for required items in crafting recipe of a tool.
    
    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param item_display_name: Display name of the item
    :type item_display_name: str
    :param required_quantity: Required quantity of the item
    :type required_quantity: int
    """

    item_unique_name: str
    item_display_name: str
    required_quantity: int

class CraftableTool(BaseModel):
    """
    The main model for the crafting recipes of a tool, including all the input items required.

    :param unique_tool_name: Unique name of the tool
    :type unique_tool_name: str
    :param display_name: Display name of the tool
    :type display_name: str
    :param required_items: List of required items for crafting the tool
    :type required_items: List[RequiredItem]
    :param category: Category of the tool
    :type category: str
    :param minimum_category_level: Minimum category level to craft the tool
    :type minimum_category_level: int
    """

    unique_tool_name: str
    display_name: str
    tier: int
    required_items: List[RequiredItem]
    category: str
    minimum_category_level: int

class InputItem(BaseModel):
    """
    Model for input items in crafting recipe of an item.
    
    :param input_item_unique_name: Unique name of the input item
    :type input_item_unique_name: str
    :param input_item_display_name: Display name of the input item
    :type input_item_display_name: str
    :param input_item_quantity: Quantity of the input item
    :type input_item_quantity: int
    """

    input_item_unique_name: str
    input_item_display_name: str
    input_item_quantity: int

class Recipe(BaseModel):
    """
    The main model for the crafting recipes of an item, including all the input items required.
    
    :param output_item_unique_name: Unique name of the output item
    :type output_item_unique_name: str
    :param output_item_display_name: Display name of the output item
    :type output_item_display_name: str
    :param generation_duration: Generation duration of the output item
    :type generation_duration: int
    :param input_items: List of input items for crafting the output item
    :type input_items: List[InputItem]
    """

    output_item_unique_name: str
    output_item_display_name: str
    generation_duration: int
    input_items: List[InputItem]

class ToolRecipes(BaseModel):
    """
    The main model for the crafting recipes of a tool, including all the input items required.
    
    :param unique_tool_name: Unique name of the tool
    :type unique_tool_name: str
    :param tool_tier: Tier of the tool
    :type tool_tier: int
    :param recipe_list: List of crafting recipes for the tool
    :type recipe_list: List[Recipe]
    """

    unique_tool_name: str
    tool_tier: int
    recipe_list: List[Recipe]

class MarketListing(BaseModel):
    """
    Model for a single market listing. Includes all used data for a listing.
    
    :param listing_id: ID of the listing (Primary Key)
    :type listing_id: int
    :param seller_id: ID of the seller
    :type seller_id: str
    :param seller_username: Username of the seller
    :type seller_username: str
    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param item_display_name: Display name of the item
    :type item_display_name: str
    :param item_description: Description of the item
    :type item_description: Optional[str]
    :param quantity: Quantity of the item
    :type quantity: int
    :param price: Price of the item
    :type price: float
    :param list_created_at: Listing creation timestamp
    :type list_created_at: datetime
    :param expire_date: Expiry date of the listing
    :type expire_date: Optional[datetime]
    """

    id: int
    seller_id: str
    seller_username: str
    item_unique_name: str
    item_display_name: str
    item_description: Optional[str]
    quantity: int
    price: float
    list_created_at: datetime
    expire_date: Optional[datetime] = None

    class Config:
        from_attributes = True  # Use orm_mode to allow ORM objects

class MarketListingsResponse(BaseModel):
    """
    Model for a list of market listings.
    
    :param listings: List of market listings
    :type listings: List[MarketListing]
    """

    listings: List[MarketListing]

class ListItemRequest(BaseModel):
    """
    Request model for listing an item in the market.
    
    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param quantity: Quantity of the item
    :type quantity: int
    :param price: Price of the item
    :type price: float
    :param expire_date: Expiry date of the listing
    :type expire_date: Optional[datetime]
    """

    item_unique_name: str
    quantity: int
    price: float
    expire_date: Optional[datetime] = None

class ListItemResponse(BaseModel):
    """
    Response model for listing an item in the market.
    
    :param status: Status of the listing
    :type status: str
    :param message: Message of the listing
    :type message: str
    :param listing_id: ID of the listing
    :type listing_id: int
    """

    status: str
    message: str
    listing_id: int

class BuyItemRequest(BaseModel):
    """
    Request model for buying an item from the market.
    
    :param listing_id: ID of the listing
    :type listing_id: int
    :param quantity: Quantity of the item
    :type quantity: int
    """

    listing_id: int
    quantity: int

class BuyItemResponse(BaseModel):
    """
    Response model for buying an item from the market.
    
    :param status: Status of the purchase
    :type status: str
    :param message: Message of the purchase
    :type message: str
    :param total_price: Total price of the purchase
    :type total_price: float
    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param item_display_name: Display name of the item
    :type item_display_name: str
    :param quantity_bought: Quantity of the item bought
    :type quantity_bought: int
    :param buyer_gold_balance: Gold balance of the buyer
    :type buyer_gold_balance: float
    """

    status: str
    message: str
    total_price: float
    item_unique_name: str
    item_display_name: str
    quantity_bought: int
    buyer_gold_balance: float

class CancelListingRequest(BaseModel):
    """
    Request model for cancelling a listing in the market.
    
    :param listing_id: ID of the listing
    :type listing_id: int
    """

    listing_id: int

class CancelListingResponse(BaseModel):
    """
    Response model for cancelling a listing in the market.
    
    :param status: Status of the cancellation
    :type status: str
    """

    status: str
    message: str

class TransactionHistoryItem(BaseModel):
    """
    Model for a single transaction history item.

    :param item_unique_name: Unique name of the item
    :type item_unique_name: str
    :param transaction_date: Transaction date
    :type transaction_date: datetime
    :param quantity: Quantity of the item
    :type quantity: int
    :param price: Price of the item
    :type price: float
    """

    item_unique_name: str
    transaction_date: datetime
    quantity: int
    price: float

class TransactionHistoryResponse(BaseModel):
    """
    Response model for transaction history.

    :param transactions: List of transaction history items
    :type transactions: List[TransactionHistoryItem]
    """

    transactions: List[TransactionHistoryItem]