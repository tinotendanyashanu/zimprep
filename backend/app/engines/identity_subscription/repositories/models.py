"""Database models and repository interfaces.

Note: Actual database schema should be managed via migrations.
This module defines the ORM models and data access patterns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer, JSON, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """User identity model."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="active, inactive, suspended"
    )
    role_override: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Override role if not derived from account"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Account(Base):
    """Account model (billing/organizational unit)."""
    
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="individual, family, school"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="active, suspended"
    )
    owner_user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Subscription(Base):
    """Subscription model."""
    
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="free, premium, school"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="active, trial, expired, cancelled, suspended, pending"
    )
    is_trial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Null for indefinite subscriptions"
    )
    trial_end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    
    features: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of feature keys"
    )
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class FeatureFlagOverride(Base):
    """Feature flag overrides for A/B testing or beta access."""
    
    __tablename__ = "feature_flag_overrides"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Why this override exists"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Override expiration"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
