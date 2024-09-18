from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, Boolean, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from Database.database import Base
import uuid

class User(Base):
    __tablename__ = 'users'

    Id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    Username = Column(String, unique=True, nullable=False)
    Email = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=True)
    UserCreatedAt = Column(DateTime, default=datetime.now())
    Gold = Column(Float, default=10.0)
    Energy = Column(Float, default=100.0)
    TotalLevel = Column(Integer, default=1)

    # Relationships
    items = relationship('UserItem', back_populates='user')
    tools = relationship('UserTool', back_populates='user')

class Item(Base):
    __tablename__ = 'items'

    Id = Column(Integer, primary_key=True, index=True)
    UniqueName = Column(String, unique=True)  # Unique name for the item
    Name = Column(String, nullable=False)     # Display name for the item
    Category = Column(String, nullable=False) # Category of the item
    GoldValue = Column(Float, default=0.0, nullable=True)    # Gold value of the item
    Probability = Column(Float, default=1.0, nullable=True)  # Probability of getting the item
    isLegendary = Column(Boolean, default=False)    # Whether the item is legendary
    isCraftable = Column(Boolean, default=False, nullable=True)    # Whether the item is acquired by crafting
    ItemDescription = Column(String, nullable=True)   # Description of the item

    # Relationships
    user_items = relationship('UserItem', back_populates='item')
    generated_by_tools = relationship('ToolGeneratableItem', back_populates='item')

class Tool(Base):
    __tablename__ = 'tools'

    Id = Column(Integer, primary_key=True, index=True)
    UniqueName = Column(String, unique=True)    # Unique name for the tool
    Name = Column(String, nullable=False)       # Display name for the tool
    Category = Column(String, nullable=False)   # Category of the tool
    isRepeating = Column(Boolean, default=False, nullable=True) # Whether the tool is repeating
    ProbabilityBoost = Column(Float, default=1.0, nullable=True)   # Boost to the probability of generating items
    ToolDescription = Column(String, nullable=True) # Description of the tool

    # Relationships
    user_tools = relationship('UserTool', back_populates='tool')
    generatable_items = relationship('ToolGeneratableItem', back_populates='tool', cascade='all, delete-orphan')
    recipes = relationship('CraftingRecipe', back_populates='tool')

class ToolGeneratableItem(Base):
    __tablename__ = 'tool_generatable_items'

    Id = Column(Integer, primary_key=True, index=True)
    ToolUniqueName = Column(String, ForeignKey('tools.UniqueName', ondelete='CASCADE'), nullable=False)   # Tool that can generate the item
    ItemUniqueName = Column(String, ForeignKey('items.UniqueName', ondelete='CASCADE'), nullable=False)   # Item that can be generated
    # Probability field removed

    # Relationships
    tool = relationship('Tool', back_populates='generatable_items')
    item = relationship('Item', back_populates='generated_by_tools')

class CraftingRecipe(Base):
    __tablename__ = 'crafting_recipes'

    Id = Column(Integer, primary_key=True, index=True)
    InputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)    # Item required as input
    InputQuantity = Column(Integer, nullable=False)   # Quantity of the input item required   
    ToolUniqueName = Column(String, ForeignKey('tools.UniqueName'), nullable=False)   # Tool required to craft the item
    OutputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)   # Item that is crafted
    OutputQuantity = Column(Integer, nullable=False)    # Quantity of the output item
    GenerationDuration = Column(Float, default=5.0)    # Duration in seconds to generate the output item

    # Relationships
    input_item = relationship('Item', foreign_keys=[InputItemUniqueName])
    output_item = relationship('Item', foreign_keys=[OutputItemUniqueName])
    tool = relationship('Tool', foreign_keys=[ToolUniqueName], back_populates='recipes')
class UserItem(Base):
    __tablename__ = 'user_items'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    ItemId = Column(Integer, ForeignKey('items.Id'), nullable=False, unique=True)    # Item that the user has
    UniqueName = Column(String, nullable=True)   # Unique name of the item
    Quantity = Column(Integer, default=0)   # Quantity of the item that the user has with the specific item.

    # Relationships
    user = relationship('User', back_populates='items')
    item = relationship('Item', back_populates='user_items')

class UserTool(Base):
    __tablename__ = 'user_tools'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)   # User that has the tool
    ToolId = Column(Integer, ForeignKey('tools.Id'), nullable=False, unique=True)   # Tool that the user has
    Tier = Column(Integer, default=1)   # Tier of the tool
    AcquiredAt = Column(DateTime, default=datetime.now(), nullable=True)   # When the user acquired the tool
    isEnabled = Column(Boolean, default=True, nullable=True)    # Whether the tool is
    isOccupied = Column(Boolean, default=False)    # Whether the tool is currently occupied
    LastUsed = Column(DateTime, default=None, nullable=True)    # When the user last used the tool, only if it is not repeating.

    # Relationships
    user = relationship('User', back_populates='tools')
    tool = relationship('Tool', back_populates='user_tools')