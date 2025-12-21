"use client";

import { Button } from "@/components/ui/button";

interface StepSummaryProps {
  level: string;
  subjects: string[];
  goal: string;
  onConfirm: () => void;
  onEdit: (step: number) => void;
}

export function StepSummary({ level, subjects, goal, onConfirm, onEdit }: StepSummaryProps) {
  
  const formattedLevel = level === "O_LEVEL" ? "O-Level" : "A-Level";
  const formattedGoal = goal.replace("_", " "); // Simple formatter

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-8 duration-500 text-center">
      <div>
        <h2 className="text-calm-h2 mb-4">You&apos;re all set.</h2>
        <p className="text-calm-body text-base">Review your profile before we build your study plan.</p>
      </div>

      <div className="bg-zinc-50 border border-zinc-200 rounded-3xl p-8 text-left max-w-lg mx-auto space-y-6">
        
        <div className="flex items-center justify-between pb-4 border-b border-zinc-200">
           <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wide">Level</p>
              <p className="text-lg font-semibold text-foreground">{formattedLevel}</p>
           </div>
           <Button variant="ghost" size="sm" onClick={() => onEdit(1)} className="text-primary hover:text-primary/80">Edit</Button>
        </div>

        <div className="flex items-start justify-between pb-4 border-b border-zinc-200">
           <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wide mb-1">Subjects</p>
              <div className="flex flex-wrap gap-2">
                 {subjects.map(s => (
                    <span key={s} className="bg-white border border-zinc-200 px-2 py-1 rounded-md text-sm font-medium text-zinc-700">
                        {s}
                    </span>
                 ))}
              </div>
           </div>
           <Button variant="ghost" size="sm" onClick={() => onEdit(2)} className="text-primary hover:text-primary/80">Edit</Button>
        </div>

        <div className="flex items-center justify-between">
           <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wide">Goal</p>
              <p className="text-lg font-semibold text-foreground capitalize">{formattedGoal.toLowerCase()}</p>
           </div>
           <Button variant="ghost" size="sm" onClick={() => onEdit(3)} className="text-primary hover:text-primary/80">Edit</Button>
        </div>

      </div>

      <div className="pt-4">
        <Button onClick={onConfirm} size="lg" className="btn-primary h-14 px-12 text-lg w-full max-w-sm rounded-full shadow-lg hover:shadow-xl transition-all">
          Start Studying
        </Button>
      </div>
    </div>
  );
}
