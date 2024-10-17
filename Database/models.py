# Database/models.py

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, DateTime, Boolean,
    ForeignKeyConstraint, UniqueConstraint, and_
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
    market_listings = relationship('Market', back_populates='seller', cascade='all, delete-orphan')
    purchases = relationship('MarketHistory', back_populates='buyer', foreign_keys='MarketHistory.BuyerId', cascade='all, delete-orphan')
    sales = relationship('MarketHistory', back_populates='seller', foreign_keys='MarketHistory.SellerId', cascade='all, delete-orphan')

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
    input_recipes = relationship(
        'CraftingRecipe',
        back_populates='input_item',
        foreign_keys='CraftingRecipe.InputItemUniqueName'
    )
    output_recipes = relationship(
        'CraftingRecipe',
        back_populates='output_item',
        foreign_keys='CraftingRecipe.OutputItemUniqueName'
    )
    ongoing_crafting_user_tools = relationship(
        'UserTool',
        back_populates='ongoing_crafting_item',
        foreign_keys='UserTool.OngoingCraftingItemUniqueName'
    )
    market_listings = relationship('Market', back_populates='item', cascade='all, delete-orphan')
    market_listings = relationship('Market', back_populates='item', cascade='all, delete-orphan')
    market_histories = relationship('MarketHistory', back_populates='item', cascade='all, delete-orphan')

class Tool(Base):
    __tablename__ = 'tools'

    Id = Column(Integer, primary_key=True, index=True)
    UniqueName = Column(String, nullable=False)
    Name = Column(String, nullable=False)
    Category = Column(String, nullable=False)
    isRepeating = Column(Boolean, default=False, nullable=True)
    ProbabilityBoost = Column(Float, default=1.0, nullable=True)
    ToolDescription = Column(String, nullable=True)
    StorageCapacity = Column(Integer, nullable=True)
    Tier = Column(Integer, default=1, nullable=True)
    isMultipleCraftable = Column(Boolean, default=False, nullable=True)
    maxCraftingNumber = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('UniqueName', 'Tier', name='unique_tool_name_tier'),
    )

    # Relationships
    user_tools = relationship(
        'UserTool',
        back_populates='tool',
        primaryjoin="and_(Tool.UniqueName == foreign(UserTool.ToolUniqueName), Tool.Tier == foreign(UserTool.Tier))"
    )
    generatable_items = relationship(
        'ToolGeneratableItem',
        back_populates='tool',
        cascade='all, delete-orphan',
        primaryjoin="and_(Tool.UniqueName == foreign(ToolGeneratableItem.ToolUniqueName), Tool.Tier == foreign(ToolGeneratableItem.ToolTier))"
    )
    tool_crafting_recipes = relationship(
        'ToolCraftingRecipe',
        back_populates='output_tool',
        primaryjoin="and_(Tool.UniqueName == foreign(ToolCraftingRecipe.OutputToolUniqueName), Tool.Tier == foreign(ToolCraftingRecipe.OutputToolTier))"
    )
    item_crafting_recipes = relationship(
        'CraftingRecipe',
        back_populates='tool',
        foreign_keys='CraftingRecipe.ToolUniqueName, CraftingRecipe.ToolTier',
        cascade='all, delete-orphan'
    )

class ToolGeneratableItem(Base):
    __tablename__ = 'tool_generatable_items'

    Id = Column(Integer, primary_key=True, index=True)
    ToolUniqueName = Column(String, nullable=False)
    ToolTier = Column(Integer, nullable=False)
    ItemUniqueName = Column(String, ForeignKey('items.UniqueName', ondelete='CASCADE'), nullable=False)
    ResourceUniqueName = Column(String, ForeignKey('items.UniqueName', ondelete='CASCADE'), nullable=True)
    ResourceQuantity = Column(Integer, nullable=True)
    OutputItemQuantity = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        ForeignKeyConstraint(
            ['ToolUniqueName', 'ToolTier'],
            ['tools.UniqueName', 'tools.Tier'],
            ondelete='CASCADE',
            name='fk_tool_generatable_items_tool'
        ),
    )

    # Relationships
    tool = relationship(
        'Tool',
        back_populates='generatable_items',
        primaryjoin="and_(ToolGeneratableItem.ToolUniqueName == Tool.UniqueName, ToolGeneratableItem.ToolTier == Tool.Tier)"
    )
    generated_item = relationship('Item', foreign_keys=[ItemUniqueName], back_populates='generated_by_tools')
    resource_item = relationship('Item', foreign_keys=[ResourceUniqueName], back_populates='tools_requiring_this_item')

class CraftingRecipe(Base):
    __tablename__ = 'crafting_recipes'

    Id = Column(Integer, primary_key=True, index=True)
    InputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    InputQuantity = Column(Integer, nullable=False)
    ToolUniqueName = Column(String, nullable=False)
    ToolTier = Column(Integer, nullable=False)
    OutputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    OutputQuantity = Column(Integer, nullable=False)
    GenerationDuration = Column(Float, default=5.0)

    __table_args__ = (
        ForeignKeyConstraint(
            ['ToolUniqueName', 'ToolTier'],
            ['tools.UniqueName', 'tools.Tier'],
            name='fk_crafting_recipes_tool'
        ),
    )

    # Relationships
    input_item = relationship(
        'Item',
        back_populates='input_recipes',
        foreign_keys=[InputItemUniqueName]
    )
    output_item = relationship(
        'Item',
        back_populates='output_recipes',
        foreign_keys=[OutputItemUniqueName]
    )
    tool = relationship(
        'Tool',
        back_populates='item_crafting_recipes',
        foreign_keys=[ToolUniqueName, ToolTier]
    )

class ToolCraftingRecipe(Base):
    __tablename__ = 'tool_crafting_recipes'

    Id = Column(Integer, primary_key=True, index=True)
    InputItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    InputQuantity = Column(Integer, nullable=False)
    OutputToolUniqueName = Column(String, nullable=False)
    OutputToolTier = Column(Integer, nullable=False)
    GenerationDuration = Column(Float, default=1.0)

    __table_args__ = (
        ForeignKeyConstraint(
            ['OutputToolUniqueName', 'OutputToolTier'],
            ['tools.UniqueName', 'tools.Tier'],
            name='fk_tool_crafting_recipes_tool'
        ),
    )

    # Relationships
    input_item = relationship('Item', foreign_keys=[InputItemUniqueName])
    output_tool = relationship(
        'Tool',
        back_populates='tool_crafting_recipes',
        primaryjoin="and_(Tool.UniqueName == foreign(ToolCraftingRecipe.OutputToolUniqueName), Tool.Tier == foreign(ToolCraftingRecipe.OutputToolTier))"
    )

class UserItem(Base):
    __tablename__ = 'user_items'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    Username = Column(String, nullable=False)
    UniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    Quantity = Column(Integer, default=0)

    # Relationships
    user = relationship('User', back_populates='items')
    item = relationship('Item', back_populates='user_items')

class UserTool(Base):
    __tablename__ = 'user_tools'

    Id = Column(Integer, primary_key=True, index=True)
    UserId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    Username = Column(String, nullable=False)
    ToolUniqueName = Column(String, nullable=False)
    Tier = Column(Integer, nullable=False)
    AcquiredAt = Column(DateTime, default=datetime.now(), nullable=True)
    isEnabled = Column(Boolean, default=True, nullable=True)
    isOccupied = Column(Boolean, default=False)
    LastUsed = Column(DateTime, default=None, nullable=True)
    OngoingCraftingItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=True)
    OngoingRemainedQuantity = Column(Integer, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['ToolUniqueName', 'Tier'],
            ['tools.UniqueName', 'tools.Tier'],
            name='fk_user_tools_tool'
        ),
    )

    # Relationships
    user = relationship('User', back_populates='tools')
    tool = relationship(
        'Tool',
        back_populates='user_tools',
        primaryjoin="and_(UserTool.ToolUniqueName == Tool.UniqueName, UserTool.Tier == Tool.Tier)"
    )
    ongoing_crafting_item = relationship(
        'Item',
        back_populates='ongoing_crafting_user_tools',
        foreign_keys=[OngoingCraftingItemUniqueName]
    )

class Market(Base):
    __tablename__ = 'market'

    Id = Column(Integer, primary_key=True, index=True)
    SellerId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    SellerUsername = Column(String, nullable=False)
    ItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    Quantity = Column(Integer, nullable=False)
    Price = Column(Float, nullable=False)
    ListCreatedAt = Column(DateTime, default=datetime.now())
    ExpireDate = Column(DateTime, nullable=True)

    # Relationships
    seller = relationship('User', back_populates='market_listings')
    item = relationship('Item', back_populates='market_listings')
    seller = relationship('User', back_populates='market_listings')
    item = relationship('Item', back_populates='market_listings')

class MarketHistory(Base):
    __tablename__ = 'market_history'

    Id = Column(Integer, primary_key=True, index=True)
    ItemUniqueName = Column(String, ForeignKey('items.UniqueName'), nullable=False)
    Quantity = Column(Integer, nullable=False)
    Price = Column(Float, nullable=False)
    SellerId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    SellerUsername = Column(String, nullable=False)
    BuyerId = Column(pgUUID(as_uuid=True), ForeignKey('users.Id'), nullable=False)
    BuyerUsername = Column(String, nullable=False)
    BuyingDate = Column(DateTime, default=datetime.now(), nullable=False)

    # Relationships
    item = relationship('Item', back_populates='market_histories')
    buyer = relationship('User', back_populates='purchases', foreign_keys=[BuyerId])
    seller = relationship('User', back_populates='sales', foreign_keys=[SellerId])