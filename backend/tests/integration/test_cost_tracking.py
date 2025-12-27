"""Integration tests for AI cost tracking.

Tests cost tracker with real MongoDB (or mocked).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.engines.ai.ai_routing_cost_control.services.cost_tracker import CostTracker
from app.engines.ai.ai_routing_cost_control.schemas.decision import CostPolicy


@pytest.fixture
def mock_mongodb():
    """Create mock MongoDB client."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.zimprep = mock_db
    mock_db.ai_cost_tracking = mock_collection
    
    return mock_client, mock_collection


@pytest.fixture
def cost_tracker(mock_mongodb):
    """Create cost tracker with mock MongoDB."""
    mock_client, mock_collection = mock_mongodb
    return CostTracker(mongodb_client=mock_client), mock_collection


@pytest.mark.asyncio
async def test_record_usage(cost_tracker):
    """Test recording AI usage."""
    tracker, mock_collection = cost_tracker
    
    # Mock insert_one to succeed
    mock_collection.insert_one = AsyncMock()
    
    await tracker.record_usage(
        user_id="user123",
        school_id="school456",
        request_type="marking",
        model="gpt-4o",
        cost_usd=0.05,
        trace_id="trace-001"
    )
    
    # Verify insert_one was called
    assert mock_collection.insert_one.call_count == 1
    
    # Verify correct record structure
    call_args = mock_collection.insert_one.call_args
    record = call_args[0][0]
    
    assert record["user_id"] == "user123"
    assert record["school_id"] == "school456"
    assert record["model"] == "gpt-4o"
    assert record["cost_usd"] == 0.05
    assert record["trace_id"] == "trace-001"
    assert isinstance(record["timestamp"], datetime)


@pytest.mark.asyncio
async def test_get_user_cost_today(cost_tracker):
    """Test getting user's cost for today."""
    tracker, mock_collection = cost_tracker
    
    #Mock aggregate to return $5 total
    async def mock_to_list(limit):
        return [{"total": 5.0}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    cost = await tracker.get_user_cost_today("user123")
    
    assert cost == 5.0
    assert mock_collection.aggregate.call_count == 1


@pytest.mark.asyncio
async def test_get_user_cost_today_no_records(cost_tracker):
    """Test getting user's cost when no records exist."""
    tracker, mock_collection = cost_tracker
    
    # Mock aggregate to return empty result
    async def mock_to_list(limit):
        return []
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    cost = await tracker.get_user_cost_today("user123")
    
    assert cost == 0.0


@pytest.mark.asyncio
async def test_get_user_cost_month(cost_tracker):
    """Test getting user's cost for this month."""
    tracker, mock_collection = cost_tracker
    
    # Mock aggregate to return $50 total
    async def mock_to_list(limit):
        return [{"total": 50.0}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    cost = await tracker.get_user_cost_month("user123")
    
    assert cost == 50.0


@pytest.mark.asyncio
async def test_get_school_cost_month(cost_tracker):
    """Test getting school's cost for this month."""
    tracker, mock_collection = cost_tracker
    
    # Mock aggregate to return $500 total
    async def mock_to_list(limit):
        return [{"total": 500.0}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    cost = await tracker.get_school_cost_month("school456")
    
    assert cost == 500.0


@pytest.mark.asyncio
async def test_check_limits_within_limits(cost_tracker):
    """Test cost check when within limits."""
    tracker, mock_collection = cost_tracker
    
    # Mock cost queries to return low costs
    async def mock_to_list(limit):
        return [{"total": 1.0}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    policy = CostPolicy(
        daily_limit_usd=10.0,
        monthly_limit_usd=100.0,
        school_monthly_limit_usd=1000.0,
        emergency_kill_switch=False,
        allow_oss_models=True,
        auto_escalate_on_low_confidence=True,
        escalation_confidence_threshold=0.7
    )
    
    within_limits, reason = await tracker.check_limits(
        user_id="user123",
        school_id="school456",
        estimated_cost=0.05,
        cost_policy=policy,
        trace_id="trace-001"
    )
    
    assert within_limits is True
    assert "Within cost limits" in reason


@pytest.mark.asyncio
async def test_check_limits_daily_exceeded(cost_tracker):
    """Test cost check when daily limit exceeded."""
    tracker, mock_collection = cost_tracker
    
    # Mock daily cost to be $9.50 (adding $0.55 would exceed $10 limit)
    async def mock_to_list(limit):
        return [{"total": 9.50}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    policy = CostPolicy(
        daily_limit_usd=10.0,
        monthly_limit_usd=100.0,
        school_monthly_limit_usd=1000.0,
        emergency_kill_switch=False,
        allow_oss_models=True,
        auto_escalate_on_low_confidence=True,
        escalation_confidence_threshold=0.7
    )
    
    within_limits, reason = await tracker.check_limits(
        user_id="user123",
        school_id="school456",
        estimated_cost=0.55,
        cost_policy=policy,
        trace_id="trace-001"
    )
    
    assert within_limits is False
    assert "Daily cost limit exceeded" in reason


@pytest.mark.asyncio
async def test_check_limits_emergency_kill_switch(cost_tracker):
    """Test cost check with emergency kill switch activated."""
    tracker, _ = cost_tracker
    
    policy = CostPolicy(
        daily_limit_usd=10.0,
        monthly_limit_usd=100.0,
        school_monthly_limit_usd=1000.0,
        emergency_kill_switch=True,  # ACTIVE
        allow_oss_models=True,
        auto_escalate_on_low_confidence=True,
        escalation_confidence_threshold=0.7
    )
    
    within_limits, reason = await tracker.check_limits(
        user_id="user123",
        school_id="school456",
        estimated_cost=0.01,
        cost_policy=policy,
        trace_id="trace-001"
    )
    
    assert within_limits is False
    assert "Emergency cost control activated" in reason


@pytest.mark.asyncio
async def test_get_remaining_budget(cost_tracker):
    """Test getting remaining budget."""
    tracker, mock_collection = cost_tracker
    
    # Mock different costs for different queries
    call_count = [0]
    
    async def mock_to_list(limit):
        call_count[0] += 1
        # First call: daily cost = $2
        # Second call: monthly cost = $20
        # Third call: school monthly = $200
        if call_count[0] == 1:
            return [{"total": 2.0}]
        elif call_count[0] == 2:
            return [{"total": 20.0}]
        else:
            return [{"total": 200.0}]
    
    mock_cursor = MagicMock()
    mock_cursor.to_list = mock_to_list
    mock_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    policy = CostPolicy(
        daily_limit_usd=10.0,
        monthly_limit_usd=100.0,
        school_monthly_limit_usd=1000.0,
        emergency_kill_switch=False,
        allow_oss_models=True,
        auto_escalate_on_low_confidence=True,
        escalation_confidence_threshold=0.7
    )
    
    budget = await tracker.get_remaining_budget(
        user_id="user123",
        school_id="school456",
        cost_policy=policy
    )
    
    assert budget["daily_remaining"] == 8.0  # 10 - 2
    assert budget["monthly_remaining"] == 80.0  # 100 - 20
    assert budget["school_monthly_remaining"] == 800.0  # 1000 - 200


@pytest.mark.asyncio
async def test_cost_tracker_disabled_when_no_client():
    """Test that cost tracker is disabled when no MongoDB client provided."""
    tracker = CostTracker(mongodb_client=None)
    
    assert tracker.tracking_enabled is False
    
    # All methods should return 0 or succeed with no-op
    assert await tracker.get_user_cost_today("user123") == 0.0
    assert await tracker.get_user_cost_month("user123") == 0.0
    assert await tracker.get_school_cost_month("school456") == 0.0
    
    # record_usage should not raise
    await tracker.record_usage(
        user_id="user123",
        school_id="school456",
        request_type="marking",
        model="gpt-4o",
        cost_usd=0.05,
        trace_id="trace-001"
    )
