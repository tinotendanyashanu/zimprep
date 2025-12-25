"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HistoryList } from "@/components/history/history-list";
import { executePipeline } from "@/lib/api-client";
import { getUser } from "@/lib/auth";
import { LoadingState } from "@/components/system/LoadingState";
import { useRouter } from "next/navigation";

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
        const user = getUser();
        if (!user) {
            router.replace('/login');
            return;
        }

        try {
            // Execute dashboard pipeline with history scope
            const response = await executePipeline("student_dashboard_v1", {
                user_id: user.id,
                role: "student",
                reporting_scope: "history",
                trace_id: crypto.randomUUID(), 
                exam_session_id: null 
            });

            // Extract history data
            const reportingOutput = response.engine_outputs?.reporting?.data_payload 
                                 || response.engine_outputs?.reporting 
                                 || response.engine_outputs?.history;
            
            const historyData = reportingOutput?.history || [];
            
            // Map to frontend shape
            const mappedHistory = historyData.map((item: any) => ({
                id: item.trace_id || item.exam_id,
                subject: item.exam_name.split(' - ')[0] || item.exam_name,
                paper: item.exam_name.split(' - ')[1] || 'Paper 1',
                date: new Date(item.date).toLocaleDateString(),
                score: item.marks,
                totalScore: item.max_marks,
                grade: item.grade
            }));

            setHistory(mappedHistory);
        } catch (err) {
            console.error("Failed to load history:", err);
            setError("Failed to load history.");
        } finally {
            setLoading(false);
        }
    }

    loadHistory();
  }, [router]);

  if (loading) {
      return <div className="h-screen flex items-center justify-center"><LoadingState variant="spinner" text="Loading history..." /></div>;
  }

  return (
    <div className="min-h-screen bg-zinc-50/50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-4 mb-8">
            <Link href="/dashboard">
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <ArrowLeft className="w-4 h-4" />
                </Button>
            </Link>
            <div>
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Attempt History</h1>
                <p className="text-zinc-500">Your past examination performance.</p>
            </div>
        </div>
      
        <main className="animate-in fade-in duration-500 delay-100">
            {error ? (
                <div className="p-4 bg-red-50 text-red-600 rounded-lg border border-red-100 text-center">
                    {error}
                </div>
            ) : (
                <HistoryList attempts={history} />
            )}
        </main>
      </div>
    </div>
  );
}
