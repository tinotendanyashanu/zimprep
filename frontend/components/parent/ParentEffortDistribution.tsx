import React from 'react';

export function ParentEffortDistribution() {
  // Mock data for effort
  const distribution = [
      { subject: "Math", percentage: 45, color: "bg-blue-500" },
      { subject: "Science", percentage: 30, color: "bg-emerald-500" },
      { subject: "English", percentage: 15, color: "bg-orange-500" },
      { subject: "Other", percentage: 10, color: "bg-zinc-300 dark:bg-zinc-700" },
  ];

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-[2rem] p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-shadow duration-300 h-full">
        <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-500 dark:text-zinc-400 mb-6">Effort Distribution</h3>
        
        {/* Stacked Bar */}
        <div className="w-full h-4 rounded-full overflow-hidden flex mb-6">
            {distribution.map((item, i) => (
                <div key={i} style={{ width: `${item.percentage}%` }} className={item.color} />
            ))}
        </div>

        {/* Legend */}
        <div className="space-y-3">
            {distribution.map((item, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${item.color}`} />
                        <span className="font-semibold text-zinc-700 dark:text-zinc-300">{item.subject}</span>
                    </div>
                    <span className="text-zinc-500 dark:text-zinc-400 tabular-nums">{item.percentage}%</span>
                </div>
            ))}
        </div>
    </div>
  );
}
