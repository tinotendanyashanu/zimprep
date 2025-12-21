import React from 'react';
import Link from 'next/link';
import { ParentOverviewCard, ParentOverviewData } from '@/components/parent/ParentOverviewCard';
import { ParentHeader } from '@/components/parent/ParentHeader';
import { ParentWeeklyTrend } from '@/components/parent/ParentWeeklyTrend';
import { ParentEffortDistribution } from '@/components/parent/ParentEffortDistribution';
import { ArrowRight, ChevronRight } from 'lucide-react';

// MOCK DATA - To be replaced by API call later
const MOCK_PARENT_OVERVIEW: ParentOverviewData = {
  student_name: "Tino",
  exam_level: "ZIMSEC O-Level",
  subjects: ["Mathematics", "English Language", "Combined Science", "History"],
  total_attempts: 42,
  last_activity: "21 Dec 2025",
  engagement_status: "CONSISTENT"
};

export default function ParentDashboardPage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <ParentHeader />
      
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-12 md:py-20">
        
        {/* Header Area - text-calm typography */}
        <div className="mb-12 space-y-4">
          <h1 className="text-calm-h2">
            Overview
          </h1>
          <p className="text-calm-body max-w-2xl">
            Latest insights into engagement and academic focus.
          </p>
        </div>

        {/* Primary Overview Section */}
        <section className="mb-8">
            <ParentOverviewCard data={MOCK_PARENT_OVERVIEW} />
        </section>

        {/* New Insights Row */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
            <div className="h-full">
                <ParentWeeklyTrend />
            </div>
            <div className="h-full">
                <ParentEffortDistribution />
            </div>
        </section>

        {/* Subject Navigation List */}
        <section className="space-y-8">
            <div className="flex items-end justify-between border-b border-border/40 pb-4">
                <h2 className="text-calm-h3">
                  Subject Details
                </h2>
                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Select to view</span>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
                {MOCK_PARENT_OVERVIEW.subjects.map((subject) => (
                    <Link 
                        key={subject} 
                        href={`/parent/subjects/${encodeURIComponent(subject)}`}
                        className="group flex items-center justify-between p-8 bg-white dark:bg-zinc-900 rounded-[2rem] border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 hover:shadow-md transition-all duration-300"
                    >
                        <span className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 group-hover:text-primary transition-colors">
                            {subject}
                        </span>
                        <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
                            <ArrowRight className="w-5 h-5 text-zinc-900 dark:text-zinc-100 group-hover:text-white" />
                        </div>
                    </Link>
                ))}
            </div>
        </section>

      </main>
    </div>
  );
}
