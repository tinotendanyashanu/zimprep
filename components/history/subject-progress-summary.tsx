"use client";

import { SubjectProgress } from "@/lib/history/types";
import { Card } from "@/components/ui/card";
import { Calculator, Trophy, History } from "lucide-react";

interface SubjectProgressSummaryProps {
  progress: SubjectProgress;
}

export function SubjectProgressSummary({ progress }: SubjectProgressSummaryProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <Card className="p-6 bg-white border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-zinc-50 rounded-xl text-zinc-500">
            <History className="w-6 h-6" />
        </div>
        <div>
            <p className="text-sm font-medium text-zinc-500">Total Attempts</p>
            <h3 className="text-2xl font-bold text-zinc-900">{progress.attempts}</h3>
        </div>
      </Card>

      <Card className="p-6 bg-white border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-zinc-50 rounded-xl text-zinc-500">
            <Calculator className="w-6 h-6" />
        </div>
        <div>
            <p className="text-sm font-medium text-zinc-500">Average Score</p>
            <h3 className="text-2xl font-bold text-zinc-900">{progress.average_score}%</h3>
        </div>
      </Card>

      <Card className="p-6 bg-white border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-zinc-50 rounded-xl text-zinc-500">
            <Trophy className="w-6 h-6" />
        </div>
        <div>
            <p className="text-sm font-medium text-zinc-500">Best Score</p>
            <h3 className="text-2xl font-bold text-zinc-900">{progress.best_score}%</h3>
        </div>
      </Card>
    </div>
  );
}
