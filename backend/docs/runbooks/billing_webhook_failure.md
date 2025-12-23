# RUNBOOK: Billing Webhook Failure

**Phase B5: Incident Response**  
**Severity**: MEDIUM  
**Last Updated**: 2025-12-23

## Overview

Handles failures in billing provider webhooks (Stripe, Paddle) that notify ZimPrep of subscription changes, preventing automatic entitlement updates.

## Detection Signals

- `zimprep_billing_webhook_failures_total` metric increase
- Webhook signature validation failures
- Timeout errors (webhook endpoint unreachable)
- Customer reports: "Paid but features not unlocked"

## Impact

- New subscriptions not activated automatically
- Cancellations not processed
- Usage limits not updated
- Revenue recognition delays

## Immediate Actions

### 1. Verify Webhook Status

```bash
# Check recent webhook logs
kubectl logs -l app=zimprep-api --tail=100 | grep "billing_webhook"

# Query billing provider dashboard
# Stripe: https://dashboard.stripe.com/webhooks
# Check for delivery failures
```

### 2. Manual Reconciliation

```bash
# Fetch subscription events from provider
python scripts/billing/sync_subscriptions.py --since="24h"

# Compare with database
python scripts/billing/reconcile_entitlements.py --fix

# Output: List of discrepancies and fixes applied
```

### 3. Notify Affected Users

```bash
# Identify users with pending changes
python scripts/billing/find_affected_users.py --output=affected_users.csv

# Send apology email + confirmation
python scripts/billing/notify_billing_sync.py --users=affected_users.csv
```

## Recovery

### Fix Webhook Endpoint

```bash
# If endpoint down, redeploy
kubectl rollout restart deployment/zimprep-api

# Verify webhook endpoint
curl -X POST https://api.zimprep.com/webhooks/billing/stripe \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'
```

### Backfill Missed Events

```bash
# Process all events from downtime period
python scripts/billing/backfill_webhooks.py \
  --start="2025-12-23T10:00:00Z" \
  --end="2025-12-23T14:00:00Z"
```

## Data Integrity Checks

```bash
# Verify no duplicate charges
python scripts/billing/check_duplicates.py

# Verify entitlements match subscriptions
python scripts/billing/verify_entitlements.py --report
```

## Escalation

**Timeframe**: If unresolved >4 hours  
**Contact**: Finance team + Engineering Lead  
**Action**: Manual subscription management

---

**Prevention**:
- Webhook retry logic
- Idempotency keys
- Daily reconciliation jobs
- Monitoring alerts
