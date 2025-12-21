import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function ParentWeeklyTrend() {
  // Mock data for last 7 days activity (1=active, 0=inactive)
  const activityData = [1, 1, 0, 1, 1, 1, 1]; 
    const trend: "up" | "down" | "stable" = "up";

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-[2rem] p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col justify-between h-full">
        <div>
            <div className="flex items-center justify-between mb-4">
                 <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">Weekly Momentum</h3>
                 {(trend as "up" | "down" | "stable") === 'up' && <TrendingUp className="w-5 h-5 text-emerald-500" />}
                 {(trend as "up" | "down" | "stable") === 'down' && <TrendingDown className="w-5 h-5 text-orange-500" />}
                 {(trend as "up" | "down" | "stable") === 'stable' && <Minus className="w-5 h-5 text-zinc-400" />}
            </div>
            
             <p className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
                Strong Pace
            </p>
             <p className="text-sm text-zinc-500 mt-1">
                Active 6 of last 7 days
            </p>
        </div>

        {/* Visual Bar Chart */}
        <div className="flex items-end gap-2 h-16 mt-6">
            {activityData.map((active, i) => (
                <div 
                    key={i} 
                    className={`flex-1 rounded-sm transition-all duration-500 ${active ? 'bg-emerald-500 dark:bg-emerald-500 h-full opacity-80 hover:opacity-100' : 'bg-zinc-100 dark:bg-zinc-800 h-2'}`}
                />
            ))}
        </div>
    </div>
  );
}
