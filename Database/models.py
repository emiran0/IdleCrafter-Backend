# Database/models.py

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as pgUUID
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
    UniqueName = Column(String, unique=True, nullable=False)
    Name = Column(String, nullable=False)
    Category = Column(String, nullable=False)
    GoldValue = Column(Float, default=0.0, nullable=True)
    Probability = Column(Float, default=1.0, nullable=True)
    isLegendary = Column(Boolean, default=False)
    isCraftable = Column(Boolean, default=False, nullable=True)
    ItemDescription = Column(String, nullable=True)

    # Relationships
    user_items = relationship('UserItem', back_populates='item')
    generated_by_tools = relationship(
        'ToolGeneratableItem',
        back_populates='generated_item',
        foreign_keys='ToolGeneratableItem.ItemUniqueName',
        cascade='all, delete-orphan'
    )
    tools_requiring_this_item = relationship(
        'ToolGeneratableItem',
        back_populates='resource_item',
        foreign_keys='ToolGeneratableItem.ResourceUniqueName',
    )

class Tool(Base):
    __tablename__ = 'tools'

    Id = Column(Integer, primary_key=True, index=True)
    UniqueName = Column(String, nullable=False)    # Unique name for the tool
    Name = Column(String, nullable=False)          # Display name for the tool
    Category = Column(String, nullable=False)      # Category of the tool
    isRepeating = Column(Boolean, default=False, nullable=True)  # Whether the tool is repeating
    ProbabilityBoost = Column(Float, default=1.0, nullable=True) # Boost to the probability of generating items
    ToolDescription = Column(String, nullable=True)              # Description of the tool
    StorageCapacity = Column(Integer, nullable=True)             # Storage capacity of the tool

    # New columns
    Tier = Column(Integer, default=1, nullable=True)                 # Tier of the tool
    isMultipleCraftable = Column(Boolean, default=False, nullable=True)  # Whether multiple instances can be crafted
    maxCraftingNumber = Column(Integer, nullable=True)               # Max instances a user can have

    # Relationships
    user_tools = relationship('UserTool', back_populates='tool')
    generatable_items = relationship(
        'ToolGeneratableItem',
        back_populates='tool',
        cascade='all, delete-orphan'
    )
    recipes = relationship('ToolCraftingRecipe', back_populates='output_tool')

class ToolGeneratableItem(Base):
    __tablename__ = 'tool_generatable_items'

    Id = Column(Integer, primary_key=True, index=True)
    ToolUniqueName = Column(String, ForeignKey('tools.UniqueName', ondelete='CASCADE'), nullable=False)
    ItemUniqueName = Column(String, ForeignKey('items.UniqueName', ondelete='CASCADE'), nullable=False)
    ResourceUniqueName = Column(String, ForeignKey('items.UniqueName', ondelete='CASCADE'), nullable=True)
    ResourceQuantity = Column(Integer, nullable=True)
    OutputItemQuantity = Column(Integer, nullable=False, default=1)

    # Relationships
    tool = relationship('Tool', back_populates='generatable_items')
    generated_item = relationship('Item', foreign_keys=[ItemUniqueName], back_populates='generated_by_tools')
    resource_item = relationship('Item', foreign_keys=[ResourceUniqueName], back_populates='tools_requiring_this_item')

class ToolCraftingRecipe(Base):
    __tablename__ = 'tool_crafting_recipes'

    Id = Column(Integer, primary_key=True, index=True)
    InputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    InputQuantity = Column(Integer, nullable=False)
    OutputToolUniqueName = Column(String, ForeignKey('tools.UniqueName'), nullable=False)
    OutputToolTier = Column(Integer, nullable=False)
    GenerationDuration = Column(Float, default=1.0)  # Duration in seconds to craft the tool

    # Relationships
    input_item = relationship('Item', foreign_keys=[InputItemUniqueName])
    output_tool = relationship(
        'Tool',
        primaryjoin="and_(Tool.UniqueName == ToolCraftingRecipe.OutputToolUniqueName, Tool.Tier == ToolCraftingRecipe.OutputToolTier)",
        back_populates='recipes'
    )

class UserItem(Base):
    __tablename__ = 'user_items'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    Username = Column(String, nullable=False)   # Username of the user
    UniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)   # Unique name of the item
    Quantity = Column(Integer, default=0)       # Quantity of the item that the user has

    # Relationships
    user = relationship('User', back_populates='items')
    item = relationship('Item', back_populates='user_items')

class UserTool(Base):
    __tablename__ = 'user_tools'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)   # User that has the tool
    Username = Column(String, nullable=False)                                       # Username of the user
    ToolUniqueName = Column(String, ForeignKey('tools.UniqueName'), nullable=False) # Tool that the user has
    Tier = Column(Integer, nullable=False)                                          # Tier of the tool
    AcquiredAt = Column(DateTime, default=datetime.now(), nullable=True)            # When the user acquired the tool
    isEnabled = Column(Boolean, default=True, nullable=True)                        # Whether the tool is enabled
    isOccupied = Column(Boolean, default=False)                                     # Whether the tool is currently occupied
    LastUsed = Column(DateTime, default=None, nullable=True)                        # When the user last used the tool, only if it is not repeating
    OngoingCraftingItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=True)  # The item currently being crafted
    OngoingRemainedQuantity = Column(Integer, nullable=True)                        # The remaining quantity to be crafted

    # Relationships
    user = relationship('User', back_populates='tools')
    tool = relationship(
        'Tool',
        primaryjoin="and_(Tool.UniqueName == UserTool.ToolUniqueName, Tool.Tier == UserTool.Tier)",
        back_populates='user_tools'
    )