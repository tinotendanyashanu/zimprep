import React from 'react';
import { cn } from "@/lib/utils";

interface ReadOnlyProgressIndicatorProps {
  value: number; // 0-100
  label?: string;
  className?: string;
}

export function ReadOnlyProgressIndicator({ value, label, className }: ReadOnlyProgressIndicatorProps) {
  // Clamp value
  const clampedValue = Math.min(Math.max(value, 0), 100);

  return (
    <div className={cn("space-y-3 w-full", className)}>
      {label && (
        <div className="flex justify-between items-end">
          <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-semibold">{label}</span>
          <span className="text-sm font-mono text-zinc-900 dark:text-zinc-100">{clampedValue}%</span>
        </div>
      )}
      <div className="h-2 w-full bg-zinc-100 dark:bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
        <div 
          className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 dark:from-emerald-500 dark:to-emerald-300 rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(16,185,129,0.3)]"
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
}
