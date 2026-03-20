'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

/**
 * Paystack redirects here after a transaction attempt.
 * URL contains: ?trxref=<ref>&reference=<ref>
 *
 * The webhook already handles provisioning; this page just gives
 * the user feedback and sends them to the dashboard.
 */
export default function SubscriptionCallbackPage() {
  const router = useRouter();
  const params = useSearchParams();
  // Flutterwave redirects with ?transaction_id=<id>&tx_ref=<ref>&status=<status>
  const transactionId = params.get('transaction_id');
  const txRef = params.get('tx_ref');
  const paymentStatus = params.get('status');
  const reference = transactionId ?? txRef;
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    if (!reference || paymentStatus === 'cancelled') {
      setStatus('error');
      return;
    }
    // The webhook will have already provisioned access.
    // Give it a brief moment then redirect.
    const timer = setTimeout(() => {
      setStatus('success');
      setTimeout(() => router.replace('/dashboard'), 1500);
    }, 2000);
    return () => clearTimeout(timer);
  }, [reference, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4 max-w-sm mx-auto px-4">
        {status === 'loading' && (
          <>
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">Confirming your payment…</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="text-2xl font-semibold">Payment received</div>
            <p className="text-muted-foreground">Taking you to your dashboard…</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="text-2xl font-semibold">Something went wrong</div>
            <p className="text-muted-foreground">
              No payment reference found. Please check your email for confirmation.
            </p>
            <button
              onClick={() => router.replace('/subscription')}
              className="mt-4 underline text-sm text-primary"
            >
              Back to plans
            </button>
          </>
        )}
      </div>
    </div>
  );
}
