"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Stats = {
  flagged_attempts: number;
  diagram_review_count: number;
  papers: number;
  papers_processing: number;
  papers_error: number;
};

type TaskCard = {
  title: string;
  description: string;
  count: number | null;
  href: string;
  urgent?: boolean;
};

export default function WorkstationPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [name, setName] = useState<string>("");

  useEffect(() => {
    createClient().auth.getSession().then(async ({ data: { session } }) => {
      if (!session) return;
      const token = session.access_token;

      const [meRes, statsRes] = await Promise.allSettled([
        fetch(`${BACKEND}/admin/employees/me`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${BACKEND}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (meRes.status === "fulfilled" && meRes.value.ok) {
        const me = await meRes.value.json();
        setName(me.name ?? "");
      }
      if (statsRes.status === "fulfilled" && statsRes.value.ok) {
        setStats(await statsRes.value.json());
      }
    });
  }, []);

  const cards: TaskCard[] = [
    {
      title: "Flagged attempts",
      description: "Student answers flagged for question or marking issues",
      count: stats?.flagged_attempts ?? null,
      href: "/workstation/flagged",
      urgent: (stats?.flagged_attempts ?? 0) > 0,
    },
    {
      title: "Review queue",
      description: "Questions with extraction issues that need manual correction",
      count: null,
      href: "/workstation/review",
    },
    {
      title: "Diagram review",
      description: "Questions with failed diagram extraction awaiting manual fix",
      count: stats?.diagram_review_count ?? null,
      urgent: (stats?.diagram_review_count ?? 0) > 0,
      href: "/workstation/diagrams",
    },
    {
      title: "Upload paper",
      description: "Upload a new past paper PDF to be processed",
      count: null,
      href: "/workstation/upload",
    },
    {
      title: "Papers",
      description: `${stats?.papers_processing ?? 0} processing · ${stats?.papers_error ?? 0} with errors`,
      count: stats?.papers ?? null,
      href: "/workstation/papers",
    },
  ];
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Greeting */}
      <div>
        <h1 className="text-xl font-semibold text-foreground">
          {greeting}{name ? `, ${name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">Here&apos;s your workstation overview.</p>
      </div>

      {/* Task cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group relative bg-card border border-border rounded-2xl p-5 hover:border-primary/40 hover:shadow-sm transition-all"
          >
            {card.urgent && (
              <span className="absolute top-4 right-4 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            )}
            <div className="space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {card.title}
                </p>
                {card.count !== null && (
                  <span className={`text-lg font-bold tabular-nums ${card.urgent ? "text-red-500" : "text-foreground"}`}>
                    {card.count}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{card.description}</p>
            </div>
            <div className="mt-4 flex items-center gap-1 text-xs text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              Open
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      {/* Help text */}
      <div className="bg-muted/40 rounded-2xl p-4 text-xs text-muted-foreground space-y-1">
        <p className="font-medium text-foreground">How this works</p>
        <ul className="space-y-0.5 list-disc list-inside">
          <li>Check <strong>Flagged attempts</strong> first — students are waiting on these.</li>
          <li>Work through the <strong>Review queue</strong> to approve extracted questions.</li>
          <li>Use <strong>Upload paper</strong> to add new past paper PDFs.</li>
        </ul>
      </div>
    </div>
  );
}
