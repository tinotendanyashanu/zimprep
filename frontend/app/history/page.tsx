"use client";

import { HistoryList } from "@/components/history/history-list";
import { getHistory } from "@/lib/history/data";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HistoryPage() {
  const history = getHistory();

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-4 mb-8">
            <Link href="/dashboard">
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <ArrowLeft className="w-4 h-4" />
                </Button>
            </Link>
            <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Practice History</h1>
                <p className="text-gray-500">A chronological record of your work.</p>
            </div>
        </div>

        <HistoryList attempts={history} />
      </div>
    </div>
  );
}
