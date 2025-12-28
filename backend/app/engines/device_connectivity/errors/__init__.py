"""Connectivity errors."""

from app.engines.device_connectivity.errors.exceptions import (
    ConnectivityException,
    SessionPausedError,
    InvalidHeartbeatError,
)

__all__ = [
    "ConnectivityException",
    "SessionPausedError",
    "InvalidHeartbeatError",
]
