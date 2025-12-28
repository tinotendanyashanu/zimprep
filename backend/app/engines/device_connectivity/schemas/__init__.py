"""Schemas for Device Connectivity Awareness Engine."""

from app.engines.device_connectivity.schemas.input import HeartbeatInput
from app.engines.device_connectivity.schemas.output import HeartbeatOutput, ConnectivityState

__all__ = ["HeartbeatInput", "HeartbeatOutput", "ConnectivityState"]
