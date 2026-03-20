"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { adminListPapers, AdminPaper } from "@/lib/api-client";
import { LoadingState } from "@/components/system/LoadingState";
import { Button } from "@/components/ui/button";
import { Upload, CheckCircle, Clock, AlertCircle, ClipboardCheck } from "lucide-react";

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

export default function PapersListPage() {
  const [papers, setPapers] = useState<AdminPaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminListPapers()
      .then(setPapers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Papers</h1>
          <p className="text-zinc-500 text-sm mt-1">
            {papers.length} paper{papers.length !== 1 ? "s" : ""} total
          </p>
        </div>
        <Button asChild>
          <Link href="/admin/papers/upload">
            <Upload className="w-4 h-4 mr-2" /> Upload Paper
          </Link>
        </Button>
      </div>

      {loading ? (
        <LoadingState variant="spinner" text="Loading papers..." />
      ) : error ? (
        <p className="text-red-500 text-sm bg-red-50 border border-red-200 rounded-lg p-4">{error}</p>
      ) : papers.length === 0 ? (
        <div className="bg-white border border-dashed border-zinc-300 rounded-xl p-16 text-center">
          <p className="text-zinc-400 mb-4">No papers uploaded yet.</p>
          <Button asChild>
            <Link href="/admin/papers/upload">Upload your first paper</Link>
          </Button>
        </div>
      ) : (
        <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-100 bg-zinc-50">
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Subject</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Level</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Year</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Paper #</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Status</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Pending</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Approved</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-600">Rejected</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {papers.map((p) => (
                <tr key={p.id} className="border-b border-zinc-50 hover:bg-zinc-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-zinc-900">{p.subject?.name ?? "—"}</td>
                  <td className="px-4 py-3 text-zinc-500">{p.subject?.level ?? "—"}</td>
                  <td className="px-4 py-3 text-zinc-700">{p.year}</td>
                  <td className="px-4 py-3 text-zinc-700">{p.paper_number}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={p.qa_counts?.pending > 0 ? "text-orange-600 font-semibold" : "text-zinc-400"}>
                      {p.qa_counts?.pending ?? 0}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-emerald-600">{p.qa_counts?.approved ?? 0}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-red-500">{p.qa_counts?.rejected ?? 0}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button asChild size="sm" variant="outline">
                      <Link href={`/admin/papers/${p.id}`}>
                        <ClipboardCheck className="w-3.5 h-3.5 mr-1.5" />
                        QA Review
                      </Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
