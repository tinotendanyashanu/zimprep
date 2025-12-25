"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, ArrowRight, ArrowLeft } from "lucide-react";
import { IBM_Plex_Serif } from "next/font/google";
import { executePipeline } from "@/lib/api-client";
import { getUser } from "@/lib/auth";
import { LoadingState } from "@/components/system/LoadingState";
import { useRouter } from "next/navigation";

const serif = IBM_Plex_Serif({ subsets: ["latin"], weight: ["400", "500", "600"] });

export default function ResultsSummaryPage({ params }: { params: Promise<{ traceId: string }> }) {
  const { traceId } = use(params);
  const router = useRouter();
  
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadResult() {
        const user = getUser();
        if (!user) {
            router.replace('/login');
            return;
        }

        try {
            // Execute reporting pipeline in read-only mode
            const response = await executePipeline("reporting_v1", {
                user_id: user.id,
                role: "student",
                reporting_scope: "detailed",
                export_format: "json",
                read_only: true, // Tell Results engine to load persisted data
                original_trace_id: traceId, // The ID to look up
                exam_session_id: null, // Optional in dashboard/reporting
                subject_code: "UNKNOWN" // Optional or fill if known
            });

            // Extract report data
            // reporting -> data_payload
            const reportData = response.engine_outputs?.reporting?.data_payload;
            
            if (!reportData) {
                throw new Error("Report data missing from response");
            }

            setResult(reportData);
        } catch (err) {
            console.error("Failed to load result:", err);
            setError(err instanceof Error ? err.message : "Failed to load examination result.");
        } finally {
            setLoading(false);
        }
    }

    loadResult();
  }, [traceId, router]);

  if (loading) {
      return (
          <div className="h-screen flex items-center justify-center">
              <LoadingState variant="spinner" text="Retrieving examination result..." />
          </div>
      );
  }

  if (error || !result) {
      return (
        <div className="h-screen flex flex-col items-center justify-center gap-4 p-6 bg-zinc-50">
            <div className="p-4 rounded-full bg-red-100 text-red-600">
                <AlertCircle className="w-8 h-8" />
            </div>
            <h1 className="text-xl font-bold text-zinc-900">Unable to load result</h1>
            <p className="text-zinc-500 max-w-md text-center">{error || "Result not found."}</p>
            <Button onClick={() => router.push('/dashboard')} variant="outline">
                Return to Dashboard
            </Button>
        </div>
      );
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-zinc-600 hover:text-zinc-900 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Dashboard</span>
          </Link>
          <div className="flex items-center gap-2">
            <div className={`text-xs px-2 py-1 rounded bg-zinc-100 text-zinc-500 font-mono`}>
                REF: {traceId.substring(0, 8)}...
            </div>
            <div className="w-6 h-6 bg-zinc-900 rounded flex items-center justify-center">
              <span className="text-xs text-white font-bold">Z</span>
            </div>
            <span className="font-bold text-zinc-900">ZimPrep</span>
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-12 animate-in slide-in-from-bottom-4 duration-700">
        {/* Title Section */}
        <div className="mb-8 text-center">
          <h1 className={`${serif.className} text-3xl font-semibold text-zinc-900 mb-2`}>
            Examination Result
          </h1>
          <p className="text-zinc-600">
            {result.subject_name || result.subject_code || "Subject"} • {result.paper_name || "Assessment"}
          </p>
          <div className="text-xs text-zinc-400 mt-1 uppercase tracking-wider">
            Issued: {new Date(result.issued_at || Date.now()).toLocaleDateString()}
          </div>
        </div>

        {/* Primary Score Card */}
        <Card className="mb-8 border-zinc-200 shadow-sm bg-white overflow-hidden relative">
          <div className={`absolute top-0 left-0 w-full h-1 ${result.pass_status ? 'bg-emerald-500' : 'bg-red-500'}`} />
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 px-4">
              
              {/* Score Display */}
              <div className="text-center md:text-left">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">
                  Total Score
                </div>
                <div className="flex items-baseline gap-2 justify-center md:justify-start">
                  <span className="text-5xl font-bold text-zinc-900 tracking-tight">
                    {result.total_marks || result.marks || 0}
                  </span>
                  <span className="text-xl text-zinc-400 font-medium">
                    / {result.max_total_marks || result.max_marks || 100}
                  </span>
                </div>
              </div>

              {/* Grade Estimate */}
              <div className="text-center md:text-right border-t md:border-t-0 md:border-l border-zinc-100 pt-6 md:pt-0 md:pl-8 w-full md:w-auto">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">
                  Grade Awarded
                </div>
                <div className={`text-5xl font-serif ${result.pass_status ? 'text-zinc-900' : 'text-red-900'}`}>
                  {result.grade || "-"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Strengths & Weaknesses (if available) */}
        {(result.topic_performance || result.strengths || result.weaknesses) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            {/* Strengths */}
            <Card className="border-zinc-200 shadow-sm">
                <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
                <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Strong Performance
                </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                <ul className="space-y-2">
                    {(result.strengths || []).map((strength: string, i: number) => (
                    <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                        <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                        {strength}
                    </li>
                    ))}
                    {(!result.strengths || result.strengths.length === 0) && (
                        <li className="text-sm text-zinc-400 italic">No specific strengths identified.</li>
                    )}
                </ul>
                </CardContent>
            </Card>

            {/* Weaknesses */}
            <Card className="border-zinc-200 shadow-sm">
                <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
                <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    Areas to Review
                </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                <ul className="space-y-2">
                    {(result.weaknesses || []).map((weakness: string, i: number) => (
                    <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                        <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                        {weakness}
                    </li>
                    ))}
                    {(!result.weaknesses || result.weaknesses.length === 0) && (
                        <li className="text-sm text-zinc-400 italic">No specific weaknesses identified.</li>
                    )}
                </ul>
                </CardContent>
            </Card>
            </div>
        )}

        {/* Appeal CTA */}
        {result.can_appeal && (
             <div className="mb-12 bg-zinc-50 p-6 rounded-xl border border-zinc-200 flex items-center justify-between">
                <div>
                     <h4 className="font-semibold text-zinc-900">Review this result?</h4>
                     <p className="text-sm text-zinc-500">You can request a forensic reconstruction of this grade.</p>
                </div>
                <Button variant="outline" className="border-zinc-300">
                    Appeal Grade
                </Button>
             </div>
        )}

      </div>
    </main>
  );
}
