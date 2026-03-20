import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Activity, BookOpen, Layers, Zap } from 'lucide-react';

export type EngagementStatus = "CONSISTENT" | "IMPROVING" | "INCONSISTENT" | "NOT STARTED";

export interface ParentOverviewData {
  student_name: string;
  exam_level: string;
  subjects: string[];
  total_attempts: number;
  last_activity: string;
  engagement_status: EngagementStatus;
}

interface ParentOverviewCardProps {
  data: ParentOverviewData;
}

export function ParentOverviewCard({ data }: ParentOverviewCardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl mx-auto">
        
        {/* Main Status Card - Spans 2 columns */}
        <div className="md:col-span-2 bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-950 rounded-[2rem] p-8 relative overflow-hidden group hover:scale-[1.01] transition-transform duration-500 shadow-xl shadow-zinc-200/50 dark:shadow-none">
             {/* Gradient overlay for depth, kept subtle */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
            
            <div className="relative z-10 flex flex-col h-full justify-between">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-zinc-300 dark:text-zinc-600 font-bold text-xs uppercase tracking-widest mb-2">Student Profile</p>
                        <h3 className="text-3xl font-bold tracking-tight text-white dark:text-zinc-900">{data.student_name}</h3>
                        <p className="text-zinc-300 dark:text-zinc-600 text-lg font-medium">{data.exam_level}</p>
                    </div>
                    <div className="bg-white/20 dark:bg-zinc-200/50 p-3 rounded-full backdrop-blur-md">
                        <Zap className="w-6 h-6 text-yellow-300 dark:text-yellow-600 fill-current" />
                    </div>
                </div>
                
                <div className="mt-8 flex items-baseline gap-3">
                    <span className="text-5xl font-extrabold tracking-tight leading-none text-white dark:text-zinc-900">
                        {data.engagement_status.charAt(0) + data.engagement_status.slice(1).toLowerCase()}
                    </span>
                    <span className="text-zinc-300 dark:text-zinc-600 font-semibold text-lg">Engagement</span>
                </div>
            </div>
        </div>

        {/* Total Attempts Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-[2rem] p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-all duration-500 group">
             <div className="flex justify-between items-start mb-4">
                 <div className="bg-zinc-100 dark:bg-zinc-800 p-3 rounded-2xl group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/40 transition-colors duration-300">
                    <Layers className="w-6 h-6 text-zinc-900 dark:text-zinc-100 group-hover:text-emerald-700 dark:group-hover:text-emerald-300 transition-colors" />
                 </div>
             </div>
             <div>
                <p className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 tabular-nums">{data.total_attempts}</p>
                <p className="text-sm font-semibold text-zinc-600 dark:text-zinc-400 mt-1">Total Exercises</p>
             </div>
        </div>

        {/* Active Subjects Summary */}
        <div className="bg-white dark:bg-zinc-900 rounded-[2rem] p-8 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-all duration-500 group">
              <div className="flex justify-between items-start mb-4">
                 <div className="bg-zinc-100 dark:bg-zinc-800 p-3 rounded-2xl group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors duration-300">
                    <BookOpen className="w-6 h-6 text-zinc-900 dark:text-zinc-100 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors" />
                 </div>
             </div>
             <div>
                <p className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 tabular-nums">{data.subjects.length}</p>
                <p className="text-sm font-semibold text-zinc-600 dark:text-zinc-400 mt-1">Active Subjects</p>
             </div>
        </div>

        {/* Last Activity */}
        <div className="md:col-span-3 bg-emerald-50 dark:bg-zinc-900 rounded-[2rem] p-6 border border-emerald-100 dark:border-zinc-800 flex items-center justify-between group">
            <div className="flex items-center gap-4">
                 <div className="bg-emerald-100 dark:bg-emerald-900/30 p-3 rounded-full">
                    <Activity className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />
                 </div>
                 <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-emerald-800 dark:text-emerald-400 mb-0.5">Latest Activity</p>
                    <p className="text-lg font-bold text-emerald-950 dark:text-emerald-100">{data.last_activity}</p>
                 </div>
            </div>
             <Badge variant="outline" className="bg-white/80 dark:bg-zinc-800 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 font-semibold px-4 py-1">
                Active
            </Badge>
        </div>
    </div>
  );
}
