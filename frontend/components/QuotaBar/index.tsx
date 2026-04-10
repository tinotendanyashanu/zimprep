"use client";

import Link from "next/link";
import type { QuotaStatus } from "@/lib/subscription";
import { GlassCard } from "@/components/ui/glass-card";
import { motion } from "framer-motion";
import { Zap, ArrowUpRight, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  quota: QuotaStatus;
};

export function QuotaBar({ quota }: Props) {
  // Paid tiers with no limit: don't show a bar
  if (quota.limit === null) return null;

  const pct = Math.min((quota.used / quota.limit) * 100, 100);
  const exhausted = quota.used >= quota.limit;

  const barColor = exhausted
    ? "bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.4)]"
    : pct >= 80
    ? "bg-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.4)]"
    : "bg-primary shadow-[0_0_12px_rgba(0,135,95,0.4)]";

  return (
    <GlassCard className={cn(
      "p-6 border shadow-xl relative overflow-hidden",
      exhausted ? "border-red-500/20 bg-red-500/5" : "border-white/20"
    )}>
      {/* Background glow */}
      <div className={cn(
        "absolute -right-12 -top-12 w-32 h-32 blur-[60px] opacity-20 rounded-full",
        exhausted ? "bg-red-500" : "bg-primary"
      )} />

      <div className="relative z-10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className={cn(
              "p-2 rounded-xl flex items-center justify-center",
              exhausted ? "bg-red-500/10 text-red-500" : "bg-primary/10 text-primary"
            )}>
              {exhausted ? <AlertCircle className="w-4 h-4" /> : <Zap className="w-4 h-4 fill-current" />}
            </div>
            <span className="text-sm font-bold tracking-tight text-foreground">Daily Learning Quota</span>
          </div>
          <div className="text-right">
            <span className={cn(
              "text-lg font-bold tracking-tighter",
              exhausted ? "text-red-500" : "text-foreground"
            )}>
              {quota.used}<span className="text-sm text-muted-foreground opacity-60 ml-1">/ {quota.limit}</span>
            </span>
          </div>
        </div>

        <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted/20 border border-muted/5">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
            className={cn("h-full rounded-full transition-all relative overflow-hidden", barColor)}
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
          </motion.div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest opacity-80">
            {exhausted 
              ? "Limit reached — Resets at midnight" 
              : `${quota.limit - quota.used} missions remaining today`}
          </p>
          <Link
            href="/subscription/pricing"
            className={cn(
              "inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-widest transition-all px-4 py-2 rounded-full",
              exhausted 
                ? "bg-red-500 text-white shadow-lg shadow-red-500/20 hover:scale-105" 
                : "bg-primary text-white shadow-lg shadow-primary/20 hover:scale-105"
            )}
          >
            {exhausted ? "Unlock Unlimited" : "Upgrade"}
            <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </GlassCard>
  );
}
