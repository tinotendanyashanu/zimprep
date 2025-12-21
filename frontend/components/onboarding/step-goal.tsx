"use client";

import { cn } from "@/lib/utils";
import { Trophy, TrendingUp, Star } from "lucide-react";

const GOALS = [
  { id: "PASS", icon: TrendingUp, title: "Just Pass", desc: "I want to secure a pass mark." },
  { id: "IMPROVE", icon: TrendingUp, title: "Improve Grade", desc: "I want to do better than my mocks." },
  { id: "DISTINCTION", icon: Trophy, title: "Aim for Distinction", desc: "I want an 'A' grade excellence." },
];

interface StepGoalProps {
  value: string;
  onChange: (val: string) => void;
}

export function StepGoal({ value, onChange }: StepGoalProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">
      <div className="text-center">
        <h2 className="text-calm-h2 mb-2">What is your primary goal?</h2>
        <p className="text-calm-body text-base">This helps us tailor the difficulty and feedback.</p>
      </div>

      <div className="grid gap-4 max-w-xl mx-auto">
        {GOALS.map((goal) => {
          const isSelected = value === goal.id;
          const Icon = goal.icon;
          return (
            <div
              key={goal.id}
              onClick={() => onChange(goal.id)}
              className={cn(
                "cursor-pointer flex items-center gap-4 p-5 rounded-2xl border-2 transition-all duration-200",
                isSelected
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border bg-card hover:border-primary/50"
              )}
            >
              <div className={cn(
                  "p-3 rounded-full shrink-0",
                  isSelected ? "bg-primary text-white" : "bg-zinc-100 text-zinc-500"
              )}>
                 <Icon className="w-6 h-6" />
              </div>
              <div>
                  <h4 className={cn("font-bold text-lg", isSelected ? "text-primary" : "text-foreground")}>{goal.title}</h4>
                  <p className="text-sm text-muted-foreground">{goal.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
