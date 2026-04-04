"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  getSubscriptionStatus,
  type QuotaStatus,
  type Subscription,
  type QuotaError,
  type Tier,
  ApiError,
} from "@/lib/subscription";

// ── Types ──────────────────────────────────────────────────────────────────────

type UseQuotaReturn = {
  /** Current tier string */
  tier: Tier | null;
  /** Full quota status (used/limit/allowed) */
  quota: QuotaStatus | null;
  /** Active subscription row (null for free tier) */
  subscription: Subscription | null;
  /** Whether quota data is loading */
  loading: boolean;
  /**
   * Wrap any async submit call. If it throws a 402, captures the quota error
   * and shows the UpgradePrompt instead of propagating.
   * Returns the result on success, null if blocked by quota.
   */
  guardedSubmit: <T>(fn: () => Promise<T>) => Promise<T | null>;
  /** Whether the UpgradePrompt should be visible */
  showUpgrade: boolean;
  /** The quota error detail for UpgradePrompt */
  upgradeDetail: QuotaError | null;
  /** Dismiss the UpgradePrompt */
  dismissUpgrade: () => void;
  /** Manually refresh quota (call after a successful submit) */
  refreshQuota: () => void;
};

// ── Hook ───────────────────────────────────────────────────────────────────────

export function useQuota(): UseQuotaReturn {
  const [studentId, setStudentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [tier, setTier] = useState<Tier | null>(null);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [upgradeDetail, setUpgradeDetail] = useState<QuotaError | null>(null);

  // Seed student identity from Supabase session
  useEffect(() => {
    createClient()
      .auth.getSession()
      .then(({ data }) => {
        const user = data.session?.user;
        const accessToken = data.session?.access_token;
        if (user) {
          setStudentId(user.id);
          setToken(accessToken ?? null);
        }
      });
  }, []);

  const fetchStatus = useCallback(() => {
    if (!studentId) return;
    setLoading(true);
    getSubscriptionStatus(studentId, token ?? undefined)
      .then((data) => {
        setTier(data.tier);
        setQuota(data.quota);
        setSubscription(data.subscription);
      })
      .catch(() => {
        // Non-fatal — fall back to starter defaults
        setTier("starter");
        setQuota({ tier: "starter", allowed: true, used: 0, limit: 5, feature: "practice" });
        setSubscription(null);
      })
      .finally(() => setLoading(false));
  }, [studentId, token]);

  useEffect(() => {
    if (!studentId) return;
    getSubscriptionStatus(studentId, token ?? undefined)
      .then((data) => {
        setTier(data.tier);
        setQuota(data.quota);
        setSubscription(data.subscription);
      })
      .catch(() => {
        setTier("starter");
        setQuota({ tier: "starter", allowed: true, used: 0, limit: 5, feature: "practice" });
        setSubscription(null);
      })
      .finally(() => setLoading(false));
  }, [studentId, token]);

  const guardedSubmit = useCallback(
    async <T>(fn: () => Promise<T>): Promise<T | null> => {
      try {
        const result = await fn();
        // After a successful submit, bump the local used count optimistically
        setQuota((prev) =>
          prev && prev.limit !== null
            ? { ...prev, used: prev.used + 1, allowed: prev.used + 1 < prev.limit }
            : prev,
        );
        return result;
      } catch (err) {
        if (err instanceof ApiError && err.status === 402) {
          const detail = err.body as QuotaError;
          setUpgradeDetail(detail);
          setShowUpgrade(true);
          return null;
        }
        throw err; // re-throw non-quota errors
      }
    },
    [],
  );

  const dismissUpgrade = useCallback(() => {
    setShowUpgrade(false);
    setUpgradeDetail(null);
  }, []);

  return {
    tier,
    quota,
    subscription,
    loading,
    guardedSubmit,
    showUpgrade,
    upgradeDetail,
    dismissUpgrade,
    refreshQuota: fetchStatus,
  };
}
