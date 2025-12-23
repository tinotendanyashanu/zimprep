"""Billing module for ZimPrep subscription management.

This module handles payment provider integrations and subscription lifecycle
management. It is FULLY DECOUPLED from the engine orchestrator and pipelines.
"""

from app.billing.billing_adapter import BillingAdapter

__all__ = ["BillingAdapter"]
