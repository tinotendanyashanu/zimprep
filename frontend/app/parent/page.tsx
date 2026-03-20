"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ParentOverviewCard, ParentOverviewData } from '@/components/parent/ParentOverviewCard';
import { ParentHeader } from '@/components/parent/ParentHeader';
import { ParentWeeklyTrend } from '@/components/parent/ParentWeeklyTrend';
import { ParentEffortDistribution } from '@/components/parent/ParentEffortDistribution';
import { ArrowRight, Loader2 } from 'lucide-react';
import { getUser } from '@/lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const EMPTY: ParentOverviewData = {
  student_name: "—",
  exam_level: "—",
  subjects: [],
  total_attempts: 0,
  last_activity: "—",
  engagement_status: "NOT STARTED",
};

export default function ParentDashboardPage() {
  const [data, setData] = useState<ParentOverviewData>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const user = getUser();
      if (!user) { setLoading(false); setError("Not logged in."); return; }

      try {
        const res = await fetch(`${API_URL}/students/parent/${user.id}/overview`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setData(await res.json());
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load overview");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <ParentHeader />

      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-12 md:py-20">
        <div className="mb-12 space-y-4">
          <h1 className="text-calm-h2">Overview</h1>
          <p className="text-calm-body max-w-2xl">Latest insights into engagement and academic focus.</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
          </div>
        ) : error ? (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>
        ) : (
          <>
            <section className="mb-8">
              <ParentOverviewCard data={data} />
            </section>

            <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
              <div className="h-full"><ParentWeeklyTrend /></div>
              <div className="h-full"><ParentEffortDistribution /></div>
            </section>

            {data.subjects.length > 0 && (
              <section className="space-y-8">
                <div className="flex items-end justify-between border-b border-border/40 pb-4">
                  <h2 className="text-calm-h3">Subject Details</h2>
                  <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Select to view</span>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  {data.subjects.map((subject) => (
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
            )}
          </>
        )}
      </main>
    </div>
  );
}
