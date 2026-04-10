"use client";

import type { Subscription } from "@/lib/subscription";
import { GlassCard } from "@/components/ui/glass-card";
import { AlertTriangle, ArrowRight, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";

type Props = {
  subscription: Subscription;
};

export function PastDueBanner({ subscription }: Props) {
  if (subscription.status !== "past_due") return null;

  const endDate = new Date(subscription.period_end).toLocaleDateString("en-US", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <GlassCard className="p-0 border-red-500/20 bg-red-500/5 overflow-hidden shadow-2xl shadow-red-500/10 rounded-[2rem]">
      <div className="flex flex-col md:flex-row items-stretch">
        <div className="bg-red-500 p-8 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-12 h-12 text-white animate-pulse" />
        </div>
        <div className="p-10 flex-1 flex flex-col xl:flex-row items-center justify-between gap-10">
          <div className="space-y-3 text-center md:text-left">
            <h3 className="text-2xl font-bold text-red-600 flex items-center justify-center md:justify-start gap-3">
              <CreditCard className="w-6 h-6" />
              Payment Issue Detected
            </h3>
            <p className="text-muted-foreground font-medium text-lg leading-relaxed max-w-2xl">
              We were unable to process your latest subscription payment. A 7-day grace period has been granted — your access remains fully active until <span className="font-bold text-foreground underline decoration-red-500/30">{endDate}</span>.
            </p>
          </div>
          <a
            href="https://paystack.com"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full xl:w-auto"
          >
            <Button variant="destructive" className="w-full xl:w-auto h-16 px-10 text-lg font-bold group shadow-2xl shadow-red-500/30 rounded-2xl">
              Resolve Billing
              <ArrowRight className="w-6 h-6 ml-3 group-hover:translate-x-1 transition-transform" />
            </Button>
          </a>
        </div>
      </div>
    </GlassCard>
  );
}
