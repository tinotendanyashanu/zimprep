"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { CheckCircle2 } from "lucide-react";

const LEVELS = [
  { id: "O_LEVEL", title: "O-Level", desc: "ZIMSEC Ordinary Level" },
  { id: "A_LEVEL", title: "A-Level", desc: "ZIMSEC Advanced Level" },
];

interface StepLevelProps {
  value: string;
  onChange: (val: string) => void;
}

export function StepLevel({ value, onChange }: StepLevelProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">
      <div className="text-center">
        <h2 className="text-calm-h2 mb-2">What level are you preparing for?</h2>
        <p className="text-calm-body text-base">Select your current examination level.</p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
        {LEVELS.map((level) => {
          const isSelected = value === level.id;
          return (
            <div
              key={level.id}
              onClick={() => onChange(level.id)}
              className={cn(
                "cursor-pointer group relative p-6 rounded-2xl border-2 transition-all duration-200 hover:shadow-md",
                isSelected
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border bg-card hover:border-primary/50"
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl font-bold">{level.title}</span>
                {isSelected && <CheckCircle2 className="w-6 h-6 text-primary" />}
              </div>
              <p className="text-muted-foreground text-sm">{level.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
