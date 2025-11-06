"""
Bulut Backend - Database Models and Configuration
SQLAlchemy async setup with PostgreSQL/SQLite support
"""

import os
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Index
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./bulut.db"  # Default to SQLite for development
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    poolclass=NullPool if "sqlite" in DATABASE_URL else None,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class AliasModel(Base):
    """Alias registration model"""
    __tablename__ = "aliases"
    
    alias = Column(String(30), primary_key=True, index=True)
    address = Column(String(100), unique=True, nullable=False, index=True)
    signature = Column(String(200), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index('idx_alias_active', 'alias', 'is_active'),
        Index('idx_address_active', 'address', 'is_active'),
    )

class TransactionModel(Base):
    """Transaction history model"""
    __tablename__ = "transactions"
    
    id = Column(String(50), primary_key=True)
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    
    # Transaction details
    from_address = Column(String(100), nullable=False, index=True)
    to_address = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="ARC", nullable=False)
    
    # Payment metadata
    payment_type = Column(String(20), nullable=False)  # single, subscription, split
    status = Column(String(20), default="pending", nullable=False)
    memo = Column(String(500), nullable=True)
    confirmation_text = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Blockchain data
    block_number = Column(Integer, nullable=True)
    gas_used = Column(String(50), nullable=True)
    
    # Additional data (JSON for flexibility)
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_tx_from_date', 'from_address', 'created_at'),
        Index('idx_tx_to_date', 'to_address', 'created_at'),
        Index('idx_tx_status', 'status'),
    )

class SubscriptionModel(Base):
    """Recurring payment subscription model"""
    __tablename__ = "subscriptions"
    
    id = Column(String(50), primary_key=True)
    subscription_hash = Column(String(100), unique=True, nullable=False)
    
    # Subscription details
    from_address = Column(String(100), nullable=False, index=True)
    to_address = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="ARC", nullable=False)
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    
    # Status and scheduling
    status = Column(String(20), default="active", nullable=False)  # active, paused, cancelled
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    next_payment_date = Column(DateTime, nullable=False)
    
    # Payment tracking
    total_payments = Column(Integer, nullable=True)
    payments_made = Column(Integer, default=0, nullable=False)
    last_payment_date = Column(DateTime, nullable=True)
    last_payment_hash = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_sub_from_status', 'from_address', 'status'),
        Index('idx_sub_next_payment', 'next_payment_date', 'status'),
    )

class PaymentIntentModel(Base):
    """Payment intent cache (for audit trail)"""
    __tablename__ = "payment_intents"
    
    intent_id = Column(String(50), primary_key=True)
    user_address = Column(String(100), nullable=False, index=True)
    
    # Intent data
    raw_command = Column(String(500), nullable=False)
    payment_type = Column(String(20), nullable=False)
    intent_json = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending", nullable=False)  # pending, confirmed, executed, cancelled
    executed_tx_hash = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_intent_user_status', 'user_address', 'status'),
        Index('idx_intent_created', 'created_at'),
    )

class UserModel(Base):
    """User profile and preferences"""
    __tablename__ = "users"
    
    address = Column(String(100), primary_key=True)
    
    # Profile
    alias = Column(String(30), unique=True, nullable=True)
    display_name = Column(String(100), nullable=True)
    
    # Preferences
    preferred_currency = Column(String(10), default="USD", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    
    # Settings
    enable_voice = Column(Boolean, default=True, nullable=False)
    require_confirmation = Column(Boolean, default=True, nullable=False)
    
    # Stats
    total_sent = Column(Float, default=0.0, nullable=False)
    total_received = Column(Float, default=0.0, nullable=False)
    transaction_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional data
    metadata = Column(JSON, nullable=True)

# ============================================================================
# DATABASE SESSION MANAGEMENT
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session
    Use in FastAPI routes:
        async def route(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Drop all tables (for development)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    print("👋 Database connections closed")

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

class DatabaseManager:
    """Helper class for common database operations"""
    
    @staticmethod
    async def create_alias(session: AsyncSession, alias_data: dict) -> AliasModel:
        """Create new alias"""
        alias = AliasModel(**alias_data)
        session.add(alias)
        await session.flush()
        return alias
    
    @staticmethod
    async def get_alias_by_name(session: AsyncSession, alias: str) -> AliasModel:
        """Get alias by name"""
        from sqlalchemy import select
        result = await session.execute(
            select(AliasModel).where(
                AliasModel.alias == alias.lower(),
                AliasModel.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_alias_by_address(session: AsyncSession, address: str) -> AliasModel:
        """Get alias by address"""
        from sqlalchemy import select
        result = await session.execute(
            select(AliasModel).where(
                AliasModel.address == address.lower(),
                AliasModel.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_transaction(session: AsyncSession, tx_data: dict) -> TransactionModel:
        """Create new transaction"""
        transaction = TransactionModel(**tx_data)
        session.add(transaction)
        await session.flush()
        return transaction
    
    @staticmethod
    async def get_user_transactions(
        session: AsyncSession,
        address: str,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """Get transactions for user"""
        from sqlalchemy import select, or_, desc
        result = await session.execute(
            select(TransactionModel)
            .where(
                or_(
                    TransactionModel.from_address == address.lower(),
                    TransactionModel.to_address == address.lower()
                )
            )
            .order_by(desc(TransactionModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def create_subscription(session: AsyncSession, sub_data: dict) -> SubscriptionModel:
        """Create new subscription"""
        subscription = SubscriptionModel(**sub_data)
        session.add(subscription)
        await session.flush()
        return subscription
    
    @staticmethod
    async def get_active_subscriptions(session: AsyncSession, address: str) -> list:
        """Get active subscriptions for user"""
        from sqlalchemy import select
        result = await session.execute(
            select(SubscriptionModel)
            .where(
                SubscriptionModel.from_address == address.lower(),
                SubscriptionModel.status == "active"
            )
            .order_by(SubscriptionModel.next_payment_date)
        )
        return result.scalars().all()
    
    @staticmethod
    async def create_payment_intent(session: AsyncSession, intent_data: dict) -> PaymentIntentModel:
        """Create payment intent record"""
        intent = PaymentIntentModel(**intent_data)
        session.add(intent)
        await session.flush()
        return intent
    
    @staticmethod
    async def get_or_create_user(session: AsyncSession, address: str) -> UserModel:
        """Get existing user or create new one"""
        from sqlalchemy import select
        result = await session.execute(
            select(UserModel).where(UserModel.address == address.lower())
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = UserModel(address=address.lower())
            session.add(user)
            await session.flush()
        
        return user

# ============================================================================
# MIGRATION SCRIPT
# ============================================================================

async def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    await init_db()
    print("✅ Migrations completed")

if __name__ == "__main__":
    import asyncio
    
    # Run migrations
    asyncio.run(run_migrations())