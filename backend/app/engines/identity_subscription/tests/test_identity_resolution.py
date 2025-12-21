"""Test identity resolution logic.

Tests user identity resolution from auth context with fail-closed behavior.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from app.engines.identity_subscription.services.identity_resolver import IdentityResolver
from app.engines.identity_subscription.schemas.input import AuthContext
from app.engines.identity_subscription.schemas.entitlements import ResolvedIdentity
from app.engines.identity_subscription.repositories.models import User, Account
from app.engines.identity_subscription.errors import IdentityResolutionError


@pytest.mark.asyncio
async def test_resolve_identity_success():
    """Test successful identity resolution."""
    resolver = IdentityResolver()
    
    # Mock repositories
    resolver.user_repo.get_by_id = AsyncMock(return_value=User(
        id="user-123",
        email="test@example.com",
        account_id="account-456",
        status="active",
        role_override=None,
        created_at=Mock(),
        updated_at=Mock()
    ))
    
    resolver.account_repo.get_by_id = AsyncMock(return_value=Account(
        id="account-456",
        name="Test Account",
        type="individual",
        status="active",
        owner_user_id="user-123",
        created_at=Mock(),
        updated_at=Mock()
    ))
    
    resolver.user_repo.is_active = Mock(return_value=True)
    resolver.account_repo.is_active = Mock(return_value=True)
    
    # Test
    auth_context = AuthContext(user_id="user-123")
    result = await resolver.resolve(auth_context, trace_id="test-trace")
    
    assert result is not None
    assert result.user_id == "user-123"
    assert result.email == "test@example.com"
    assert result.account_id == "account-456"


@pytest.mark.asyncio
async def test_resolve_identity_unauthenticated():
    """Test identity resolution with no auth context."""
    resolver = IdentityResolver()
    
    result = await resolver.resolve(None, trace_id="test-trace")
    
    assert result is None


@pytest.mark.asyncio
async def test_resolve_identity_user_not_found():
    """Test identity resolution when user not found."""
    resolver = IdentityResolver()
    
    resolver.user_repo.get_by_id = AsyncMock(return_value=None)
    
    auth_context = AuthContext(user_id="nonexistent")
    result = await resolver.resolve(auth_context, trace_id="test-trace")
    
    assert result is None


@pytest.mark.asyncio
async def test_resolve_identity_inactive_user():
    """Test identity resolution fails for inactive user."""
    resolver = IdentityResolver()
    
    resolver.user_repo.get_by_id = AsyncMock(return_value=User(
        id="user-123",
        email="test@example.com",
        account_id="account-456",
        status="inactive",
        role_override=None,
        created_at=Mock(),
        updated_at=Mock()
    ))
    
    resolver.user_repo.is_active = Mock(return_value=False)
    
    auth_context = AuthContext(user_id="user-123")
    
    with pytest.raises(IdentityResolutionError):
        await resolver.resolve(auth_context, trace_id="test-trace")


@pytest.mark.asyncio
async def test_resolve_identity_suspended_account():
    """Test identity resolution fails for suspended account."""
    resolver = IdentityResolver()
    
    resolver.user_repo.get_by_id = AsyncMock(return_value=User(
        id="user-123",
        email="test@example.com",
        account_id="account-456",
        status="active",
        role_override=None,
        created_at=Mock(),
        updated_at=Mock()
    ))
    
    resolver.account_repo.get_by_id = AsyncMock(return_value=Account(
        id="account-456",
        name="Test Account",
        type="individual",
        status="suspended",
        owner_user_id="user-123",
        created_at=Mock(),
        updated_at=Mock()
    ))
    
    resolver.user_repo.is_active = Mock(return_value=True)
    resolver.account_repo.is_active = Mock(return_value=False)
    
    auth_context = AuthContext(user_id="user-123")
    
    with pytest.raises(IdentityResolutionError):
        await resolver.resolve(auth_context, trace_id="test-trace")
