"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function WorkstationDiagramsPage() {
  useEffect(() => {
    createClient().auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      // Token available for future diagram-specific endpoints
    });
  }, []);

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Diagram review</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Questions with failed diagram extraction</p>
      </div>
      <div className="bg-card border border-border rounded-2xl p-6 text-center space-y-2">
        <p className="text-sm font-medium text-foreground">Diagram editor</p>
        <p className="text-xs text-muted-foreground">
          Use the full admin panel to review and fix diagrams with the built-in editor.
        </p>
        <a
          href="/admin/diagrams"
          className="inline-flex items-center gap-1.5 mt-3 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition"
        >
          Open diagram editor
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </a>
      </div>
    </div>
  );
}
