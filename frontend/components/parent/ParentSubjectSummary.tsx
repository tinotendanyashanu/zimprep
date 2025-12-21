import React from 'react';
import { ReadOnlyProgressIndicator } from './ReadOnlyProgressIndicator';
import { CheckCircle2, TrendingUp, AlertCircle, Clock } from 'lucide-react';

export interface ParentSubjectProgressData {
  subject: string;
  attempts: number;
  average_score_range: string;
  average_score_value: number;
  best_score: number;
  common_difficulties: string[];
}

interface ParentSubjectSummaryProps {
  data: ParentSubjectProgressData;
}

export function ParentSubjectSummary({ data }: ParentSubjectSummaryProps) {
  return (
    <div className="space-y-10">
      
      {/* Metrics Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Card 1: Attempts */}
        <div className="bg-white dark:bg-zinc-900 rounded-[2rem] p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col justify-between h-48 group hover:scale-[1.02] transition-transform duration-300">
            <div className="flex justify-between items-start">
               <div className="p-3 bg-zinc-100 dark:bg-zinc-800 rounded-2xl text-zinc-900 dark:text-white">
                  <Clock className="w-5 h-5" />
               </div>
            </div>
            <div>
                <p className="text-5xl font-bold tracking-tighter text-zinc-900 dark:text-white tabular-nums">
                    {data.attempts}
                </p>
                <p className="text-sm font-semibold text-zinc-600 dark:text-zinc-400 mt-2">Total Sessions</p>
            </div>
        </div>

        {/* Card 2: Avg Score - Increased contrast dark */}
        <div className="bg-zinc-900 dark:bg-zinc-200 rounded-[2rem] p-8 border border-zinc-900 dark:border-zinc-200 shadow-sm flex flex-col justify-between h-48 group hover:scale-[1.02] transition-transform duration-300">
             <div className="flex justify-between items-start">
               <div className="p-3 bg-zinc-800 dark:bg-zinc-300 rounded-2xl text-white dark:text-zinc-900">
                  <TrendingUp className="w-5 h-5" />
               </div>
            </div>
            <div>
                <p className="text-5xl font-bold tracking-tighter text-white dark:text-zinc-900 tabular-nums">
                    {data.average_score_range}
                </p>
                <p className="text-sm font-semibold text-zinc-400 dark:text-zinc-700 mt-2">Typical Score Range</p>
            </div>
        </div>

        {/* Card 3: Best Score - High Contrast Green */}
        <div className="bg-emerald-700 dark:bg-emerald-600 rounded-[2rem] p-8 border border-emerald-600 dark:border-emerald-500 shadow-lg flex flex-col justify-between h-48 group hover:scale-[1.02] transition-transform duration-300 relative overflow-hidden">
             {/* Decorative shine, lower opacity */}
             <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -mr-10 -mt-10" />
             
             <div className="flex justify-between items-start relative z-10">
               <div className="p-3 bg-white/10 rounded-2xl text-white">
                  <CheckCircle2 className="w-5 h-5" />
               </div>
               <span className="px-3 py-1 bg-black/20 rounded-lg text-xs font-bold uppercase tracking-widest text-white">
                   Personal Best
               </span>
            </div>
            <div className="relative z-10">
                <p className="text-5xl font-bold tracking-tighter text-white tabular-nums">
                    {data.best_score}%
                </p>
                <p className="text-sm font-medium text-emerald-100 mt-2">Highest Score Achieved</p>
            </div>
        </div>
      </div>

      {/* Detail Sections Grid */}
      <div className="grid gap-6 md:grid-cols-5">
        
        {/* Performance Indicator - Spans 3 */}
        <div className="md:col-span-3 bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 border border-zinc-200 dark:border-zinc-800 shadow-sm">
             <h3 className="text-xl font-bold tracking-tight mb-2 text-zinc-900 dark:text-zinc-100">Performance Output</h3>
             <p className="text-zinc-600 dark:text-zinc-400 text-sm font-medium mb-10 max-w-sm leading-relaxed">
                Comparison of recent average performance against personal bests.
             </p>
             
             <div className="space-y-10">
                <ReadOnlyProgressIndicator 
                    value={data.average_score_value} 
                    label="Current Average" 
                    className="p-1"
                />
                <ReadOnlyProgressIndicator 
                    value={data.best_score} 
                    label="Personal Record"
                    className="opacity-70"
                />
             </div>
        </div>

        {/* Areas for Review - Spans 2 */}
        <div className="md:col-span-2 bg-zinc-50 dark:bg-zinc-900/50 rounded-[2.5rem] p-8 border border-zinc-200 dark:border-zinc-800">
             <div className="flex items-center gap-3 mb-6">
                <AlertCircle className="hidden md:block w-5 h-5 text-zinc-900 dark:text-zinc-100" />
                <h3 className="text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Focus Topics</h3>
             </div>
             
             <div className="space-y-4">
                 {data.common_difficulties.length > 0 ? (
                    data.common_difficulties.map((topic, i) => (
                        <div key={i} className="group p-4 bg-white dark:bg-zinc-800 rounded-2xl border border-zinc-200 dark:border-zinc-700 shadow-sm hover:shadow-md transition-all duration-300">
                             <div className="flex items-start gap-3">
                                 <div className="w-2 h-2 rounded-full bg-orange-500 mt-1.5 shrink-0" />
                                 <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200 leading-snug">{topic}</p>
                             </div>
                        </div>
                    ))
                ) : (
                    <div className="h-full flex items-center justify-center text-center p-6">
                        <p className="text-sm font-medium text-zinc-500">No specific areas identified.</p>
                    </div>
                )}
             </div>
        </div>

      </div>
    </div>
  );
}
