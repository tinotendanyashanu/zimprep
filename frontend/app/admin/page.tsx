"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { adminListPapers, AdminPaper } from "@/lib/api-client";
import { LoadingState } from "@/components/system/LoadingState";
import { Upload, FileText, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

function StatusBadge({ status }: { status: string }) {
  if (status === "ready")
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle className="w-3 h-3" /> Ready
      </span>
    );
  if (status === "processing")
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        <Clock className="w-3 h-3" /> Processing
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200">
      <AlertCircle className="w-3 h-3" /> Error
    </span>
  );
}

export default function AdminOverviewPage() {
  const [papers, setPapers] = useState<AdminPaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminListPapers()
      .then(setPapers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const totalPending = papers.reduce((s, p) => s + (p.qa_counts?.pending ?? 0), 0);
  const totalApproved = papers.reduce((s, p) => s + (p.qa_counts?.approved ?? 0), 0);
  const processingCount = papers.filter((p) => p.status === "processing").length;

  return (
    <div className="space-y-8 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Overview</h1>
          <p className="text-zinc-500 text-sm mt-1">Manage past papers and question quality.</p>
        </div>
        <div className="flex gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/papers">View All Papers</Link>
          </Button>
          <Button asChild>
            <Link href="/admin/papers/upload">
              <Upload className="w-4 h-4 mr-2" /> Upload Paper
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Papers", value: papers.length, color: "text-zinc-900" },
          { label: "Processing", value: processingCount, color: "text-amber-600" },
          { label: "Pending QA", value: totalPending, color: "text-orange-600" },
          { label: "Approved Questions", value: totalApproved, color: "text-emerald-600" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white border border-zinc-200 rounded-xl p-5">
            <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider mb-1">{stat.label}</p>
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Recent papers */}
      <div>
        <h2 className="text-sm font-semibold text-zinc-700 uppercase tracking-wider mb-3">Recent Papers</h2>
        {loading ? (
          <LoadingState variant="spinner" text="Loading..." />
        ) : error ? (
          <p className="text-red-500 text-sm">{error}</p>
        ) : papers.length === 0 ? (
          <div className="bg-white border border-dashed border-zinc-300 rounded-xl p-12 text-center">
            <FileText className="w-8 h-8 text-zinc-300 mx-auto mb-3" />
            <p className="text-zinc-500">No papers uploaded yet.</p>
            <Button asChild className="mt-4">
              <Link href="/admin/papers/upload">Upload your first paper</Link>
            </Button>
          </div>
        ) : (
          <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-100 bg-zinc-50/50">
                  <th className="px-4 py-3 text-left font-semibold text-zinc-600">Subject</th>
                  <th className="px-4 py-3 text-left font-semibold text-zinc-600">Year</th>
                  <th className="px-4 py-3 text-left font-semibold text-zinc-600">Paper</th>
                  <th className="px-4 py-3 text-left font-semibold text-zinc-600">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-zinc-600">QA</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {papers.slice(0, 10).map((p) => (
                  <tr key={p.id} className="border-b border-zinc-50 hover:bg-zinc-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-zinc-900">
                      {p.subject?.name ?? "—"}
                      {p.subject?.level && (
                        <span className="ml-1 text-xs text-zinc-400">{p.subject.level}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-zinc-700">{p.year}</td>
                    <td className="px-4 py-3 text-zinc-700">Paper {p.paper_number}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-orange-600 font-medium">{p.qa_counts?.pending ?? 0} pending</span>
                      <span className="text-zinc-400 mx-1">/</span>
                      <span className="text-emerald-600">{p.qa_counts?.approved ?? 0} approved</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {(p.qa_counts?.pending ?? 0) > 0 && (
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/admin/papers/${p.id}`}>Review QA</Link>
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
