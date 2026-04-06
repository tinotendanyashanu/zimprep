"use client";

import { useEffect, useState } from "react";
import { MathText } from "@/components/math-text";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const REASON_LABELS: Record<string, { label: string; color: string }> = {
  marks_missing:  { label: "Marks missing",    color: "bg-orange-50 text-orange-700 border-orange-200" },
  text_too_short: { label: "Text too short",   color: "bg-red-50 text-red-700 border-red-200" },
  diagram_no_bbox:{ label: "Diagram no bbox",  color: "bg-amber-50 text-amber-700 border-amber-200" },
  student_flag:   { label: "Student reported", color: "bg-purple-50 text-purple-700 border-purple-200" },
};

type ReviewQuestion = {
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
  needs_review: boolean;
  review_reasons: string[];
  hidden: boolean;
  paper_id: string;
  paper: {
    year: number;
    paper_number: number;
    exam_session: string | null;
    subject: { name: string; level: string };
  } | null;
};

type EditState = { text: string; marks: string; topic_tags: string; question_type: string };

export default function ReviewQueuePage() {
  const [questions, setQuestions] = useState<ReviewQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState>({ text: "", marks: "", topic_tags: "", question_type: "written" });
  const [approving, setApproving] = useState<string | null>(null);
  const [discarding, setDiscarding] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    fetch(`${BACKEND}/admin/questions/review-queue?limit=200`)
      .then((r) => r.json())
      .then((d) => { setQuestions(d.questions ?? []); setTotal(d.total ?? 0); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function startEdit(q: ReviewQuestion) {
    setEditingId(q.id);
    setEditState({
      text: q.text,
      marks: String(q.marks),
      topic_tags: q.topic_tags.join(", "),
      question_type: q.question_type,
    });
    setError(null);
  }

  async function approve(q: ReviewQuestion) {
    setApproving(q.id);
    setError(null);
    const payload = editingId === q.id ? {
      text: editState.text.trim(),
      marks: parseInt(editState.marks, 10) || 0,
      topic_tags: editState.topic_tags.split(",").map((t) => t.trim()).filter(Boolean),
      question_type: editState.question_type,
    } : {};

    try {
      const res = await fetch(`${BACKEND}/admin/questions/${q.id}/approve`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? "Approve failed");
      }
      setQuestions((prev) => prev.filter((x) => x.id !== q.id));
      setTotal((t) => t - 1);
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setApproving(null);
    }
  }

  // Discard = keep hidden permanently (clears review flag, stays hidden from students)
  async function discard(q: ReviewQuestion) {
    setDiscarding(q.id);
    try {
      const res = await fetch(`${BACKEND}/admin/questions/${q.id}/discard`, { method: "PATCH" });
      if (!res.ok) throw new Error("Discard failed");
      setQuestions((prev) => prev.filter((x) => x.id !== q.id));
      setTotal((t) => t - 1);
    } catch {
      setError("Discard failed — try again");
    } finally {
      setDiscarding(null);
    }
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Question Review Queue</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Questions flagged during extraction for missing marks, short text, or missing diagram info.
            Hidden from students until approved.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {total > 0 && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-red-100 text-red-800 text-xs font-semibold border border-red-200">
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

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">
          {error}
        </p>
      )}

      {/* Empty */}
      {!loading && questions.length === 0 && (
        <div className="border border-border rounded-xl p-12 text-center">
          <svg className="w-10 h-10 text-green-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium text-foreground">Queue is clear</p>
          <p className="text-xs text-muted-foreground mt-1">No questions need review.</p>
        </div>
      )}

      {/* Skeleton */}
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
        const isEditing = editingId === q.id;
        const isApproving = approving === q.id;
        const isDiscarding = discarding === q.id;
        const busy = isApproving || isDiscarding;

        const paperLabel = q.paper
          ? `${q.paper.subject.name} · ${q.paper.year}${q.paper.exam_session ? ` (${q.paper.exam_session})` : ""} P${q.paper.paper_number}`
          : "Unknown paper";

        return (
          <div key={q.id} className="border border-border rounded-xl overflow-hidden bg-card">
            {/* Row header — click to expand */}
            <button
              className="w-full flex items-start gap-3 p-4 text-left hover:bg-muted/30 transition-colors"
              onClick={() => setExpanded(isExpanded ? null : q.id)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1.5">
                  <span className="font-mono text-xs text-muted-foreground">
                    Q{q.question_number}{q.sub_question ? `(${q.sub_question})` : ""}
                    {q.section ? ` §${q.section}` : ""}
                  </span>
                  <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                    {paperLabel}
                  </span>
                  {q.marks === 0 && (
                    <span className="text-xs text-muted-foreground italic">no marks</span>
                  )}
                  {q.marks > 0 && (
                    <span className="text-xs text-muted-foreground">{q.marks}mk</span>
                  )}
                  {q.review_reasons.map((r) => {
                    const def = REASON_LABELS[r] ?? { label: r, color: "bg-muted text-muted-foreground border-border" };
                    return (
                      <span key={r} className={`text-[11px] px-1.5 py-0.5 rounded border font-medium ${def.color}`}>
                        {def.label}
                      </span>
                    );
                  })}
                </div>
                <div className="text-sm text-foreground line-clamp-2">
                  {q.text ? <MathText text={q.text} /> : <span className="italic text-muted-foreground">No text extracted</span>}
                </div>
              </div>
              <svg
                className={`w-4 h-4 text-muted-foreground mt-1 shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>

            {/* Expanded detail + edit + actions */}
            {isExpanded && (
              <div className="border-t border-border px-4 py-4 space-y-4">
                {isEditing ? (
                  /* Edit form */
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">Question Text</label>
                      <textarea
                        rows={4}
                        value={editState.text}
                        onChange={(e) => setEditState((s) => ({ ...s, text: e.target.value }))}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-foreground mb-1">Marks</label>
                        <input
                          type="number" min={0}
                          value={editState.marks}
                          onChange={(e) => setEditState((s) => ({ ...s, marks: e.target.value }))}
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-foreground mb-1">Type</label>
                        <select
                          value={editState.question_type}
                          onChange={(e) => setEditState((s) => ({ ...s, question_type: e.target.value }))}
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        >
                          <option value="written">Written</option>
                          <option value="mcq">MCQ</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-foreground mb-1">Topic Tags</label>
                        <input
                          type="text"
                          value={editState.topic_tags}
                          onChange={(e) => setEditState((s) => ({ ...s, topic_tags: e.target.value }))}
                          placeholder="Algebra, Sets"
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Read-only view */
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Question text</p>
                    <div className="text-sm text-foreground">
                      {q.text ? <MathText text={q.text} /> : <span className="italic text-muted-foreground">Empty</span>}
                    </div>
                    {q.image_url && (
                      <div className="mt-3 rounded-xl border border-border bg-white overflow-hidden">
                        <div className="px-3 py-1.5 border-b border-border bg-muted/40 text-xs text-muted-foreground font-medium">
                          Figure / Diagram
                        </div>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={q.image_url} alt="Question diagram" className="w-full max-h-72 object-contain p-4" style={{ background: "white" }} />
                      </div>
                    )}
                  </div>
                )}

                {/* Action bar */}
                <div className="flex items-center gap-2 flex-wrap pt-1">
                  {isEditing ? (
                    <>
                      <button
                        onClick={() => approve(q)}
                        disabled={busy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
                      >
                        {isApproving ? "Approving…" : "Save & Approve"}
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        disabled={busy}
                        className="px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground disabled:opacity-50 transition-colors"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => startEdit(q)}
                        disabled={busy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-sm text-foreground hover:bg-muted/60 disabled:opacity-50 transition-colors"
                      >
                        Edit & Approve
                      </button>
                      <button
                        onClick={() => approve(q)}
                        disabled={busy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
                      >
                        {isApproving ? "Approving…" : "Approve as-is"}
                      </button>
                      <button
                        onClick={() => discard(q)}
                        disabled={busy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 text-red-700 border border-red-200 text-sm font-medium hover:bg-red-100 disabled:opacity-50 transition-colors"
                      >
                        {isDiscarding ? "Discarding…" : "Discard"}
                      </button>
                    </>
                  )}
                </div>

                <p className="text-[11px] text-muted-foreground">
                  <strong>Approve</strong> — fixes the question and makes it visible to students.{" "}
                  <strong>Discard</strong> — keeps it hidden permanently (bad extraction, not fixable).
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
