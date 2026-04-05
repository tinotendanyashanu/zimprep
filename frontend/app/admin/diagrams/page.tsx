"use client";

import { useEffect, useRef, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type DiagramQuestion = {
  id: string;
  question_number: string;
  sub_question: string | null;
  section: string | null;
  marks: number;
  text: string;
  has_image: boolean;
  image_url: string | null;
  topic_tags: string[];
  question_type: string;
  diagram_status: string;
  paper_id: string;
  paper: {
    year: number;
    paper_number: number;
    subject: { name: string; level: string };
  } | null;
};

function QuestionLabel({ q }: { q: DiagramQuestion }) {
  const parts = [`Q${q.question_number}`];
  if (q.sub_question) parts.push(q.sub_question);
  if (q.section) parts.unshift(`§${q.section}`);
  return <span className="font-mono text-xs text-muted-foreground">{parts.join(" ")}</span>;
}

function PaperBadge({ paper }: { paper: DiagramQuestion["paper"] }) {
  if (!paper) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-muted text-xs text-foreground">
      {paper.subject.name} · {paper.subject.level} · {paper.year} P{paper.paper_number}
    </span>
  );
}

export default function AdminDiagramsPage() {
  const [questions, setQuestions] = useState<DiagramQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null);
  const [dismissing, setDismissing] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  function load() {
    setLoading(true);
    fetch(`${BACKEND}/admin/questions/diagram-review?limit=100`)
      .then((r) => r.json())
      .then((d) => {
        setQuestions(d.questions ?? []);
        setTotal(d.total ?? 0);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleUpload(questionId: string, file: File) {
    setUploading(questionId);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${BACKEND}/admin/questions/${questionId}/fix-diagram`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail ?? "Upload failed");
        return;
      }
      setQuestions((prev) => prev.filter((q) => q.id !== questionId));
      setTotal((t) => t - 1);
    } catch (e) {
      alert("Upload failed");
    } finally {
      setUploading(null);
    }
  }

  async function handleNoDiagram(questionId: string) {
    setDismissing(questionId);
    try {
      const res = await fetch(`${BACKEND}/admin/questions/${questionId}/no-diagram`, {
        method: "PATCH",
      });
      if (!res.ok) {
        alert("Failed to update question");
        return;
      }
      setQuestions((prev) => prev.filter((q) => q.id !== questionId));
      setTotal((t) => t - 1);
    } catch {
      alert("Request failed");
    } finally {
      setDismissing(null);
    }
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Diagram Review</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Questions where diagram extraction failed. These are hidden from students until corrected.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {total > 0 && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-semibold border border-amber-200">
              {total} pending
            </span>
          )}
          <button
            onClick={load}
            className="px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Empty state */}
      {!loading && questions.length === 0 && (
        <div className="border border-border rounded-xl p-12 text-center">
          <svg className="w-10 h-10 text-green-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium text-foreground">All clear</p>
          <p className="text-xs text-muted-foreground mt-1">No questions pending diagram review.</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border border-border rounded-xl p-4 animate-pulse">
              <div className="h-4 bg-muted rounded w-1/3 mb-2" />
              <div className="h-3 bg-muted rounded w-2/3" />
            </div>
          ))}
        </div>
      )}

      {/* Question list */}
      {!loading && questions.map((q) => {
        const isExpanded = expanded === q.id;
        const isUploading = uploading === q.id;
        const isDismissing = dismissing === q.id;

        return (
          <div key={q.id} className="border border-border rounded-xl overflow-hidden bg-card">
            {/* Question header */}
            <button
              className="w-full flex items-start gap-3 p-4 text-left hover:bg-muted/30 transition-colors"
              onClick={() => setExpanded(isExpanded ? null : q.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <QuestionLabel q={q} />
                  <PaperBadge paper={q.paper} />
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] bg-amber-50 text-amber-700 border border-amber-200">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                    Diagram failed
                  </span>
                  <span className="text-xs text-muted-foreground">{q.marks}mk</span>
                </div>
                <p className="text-sm text-foreground line-clamp-2">{q.text}</p>
              </div>
              <svg
                className={`w-4 h-4 text-muted-foreground mt-0.5 shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>

            {/* Expanded details + actions */}
            {isExpanded && (
              <div className="border-t border-border px-4 py-4 space-y-4">
                {/* Full question text */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Question text</p>
                  <p className="text-sm text-foreground whitespace-pre-wrap">{q.text}</p>
                </div>

                {/* Current (failed) image if any */}
                {q.image_url && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                      Current image (fallback / incorrect)
                    </p>
                    <div className="border border-border rounded-lg overflow-hidden max-h-48 bg-white">
                      <img
                        src={q.image_url}
                        alt="Current diagram"
                        className="max-h-48 w-auto mx-auto object-contain p-2"
                      />
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-3 flex-wrap">
                  {/* Upload corrected image */}
                  <div>
                    <input
                      ref={(el) => { fileRefs.current[q.id] = el; }}
                      type="file"
                      accept="image/png,image/jpeg,image/svg+xml"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleUpload(q.id, file);
                        // reset so same file can be re-selected
                        e.target.value = "";
                      }}
                    />
                    <button
                      disabled={isUploading || isDismissing}
                      onClick={() => fileRefs.current[q.id]?.click()}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
                    >
                      {isUploading ? (
                        <>
                          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Uploading…
                        </>
                      ) : (
                        <>
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                          </svg>
                          Upload corrected image
                        </>
                      )}
                    </button>
                  </div>

                  {/* No diagram needed */}
                  <button
                    disabled={isUploading || isDismissing}
                    onClick={() => handleNoDiagram(q.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 disabled:opacity-50 transition-colors"
                  >
                    {isDismissing ? (
                      <>
                        <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Saving…
                      </>
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        No diagram needed
                      </>
                    )}
                  </button>
                </div>

                <p className="text-[11px] text-muted-foreground">
                  Uploading a corrected image or marking as &quot;no diagram&quot; will make this question visible to students immediately.
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
