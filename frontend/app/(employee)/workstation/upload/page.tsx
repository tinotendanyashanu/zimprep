"use client";

import { useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const LEVELS = ["Grade7", "O", "A", "IGCSE", "AS_Level", "A_Level"];
const BOARDS = ["zimsec", "cambridge"];
const SESSIONS = ["june", "november"];

export default function WorkstationUploadPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    subject_name: "",
    level: "O",
    exam_board: "zimsec",
    year: new Date().getFullYear(),
    paper_number: 1,
    exam_session: "",
    duration_minutes: 120,
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ paper_id: string } | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) { setError("Please select a PDF file"); return; }

    const { data: { session } } = await createClient().auth.getSession();
    if (!session) return;

    setSubmitting(true);
    setError("");
    setResult(null);

    const fd = new FormData();
    fd.append("file", file);
    fd.append("subject_name", form.subject_name);
    fd.append("level", form.level);
    fd.append("exam_board", form.exam_board);
    fd.append("year", String(form.year));
    fd.append("paper_number", String(form.paper_number));
    if (form.exam_session) fd.append("exam_session", form.exam_session);
    fd.append("duration_minutes", String(form.duration_minutes));

    try {
      const res = await fetch(`${BACKEND}/admin/papers/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail ?? "Upload failed");
        return;
      }
      const data = await res.json();
      setResult(data);
      setForm((f) => ({ ...f, subject_name: "", paper_number: 1 }));
      if (fileRef.current) fileRef.current.value = "";
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Upload paper</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Upload a past paper PDF to be extracted</p>
      </div>

      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-sm text-emerald-700">
          Paper uploaded — extraction running in background.
          <span className="ml-1 text-[11px] font-mono text-emerald-600">{result.paper_id}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2 space-y-1.5">
            <label className="text-xs font-medium text-foreground">Subject name</label>
            <input
              required
              type="text"
              value={form.subject_name}
              onChange={(e) => setForm((f) => ({ ...f, subject_name: e.target.value }))}
              placeholder="e.g. Mathematics"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Level</label>
            <select
              value={form.level}
              onChange={(e) => setForm((f) => ({ ...f, level: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Exam board</label>
            <select
              value={form.exam_board}
              onChange={(e) => setForm((f) => ({ ...f, exam_board: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {BOARDS.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Year</label>
            <input
              required
              type="number"
              min={2000}
              max={2030}
              value={form.year}
              onChange={(e) => setForm((f) => ({ ...f, year: Number(e.target.value) }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Paper number</label>
            <input
              required
              type="number"
              min={1}
              max={9}
              value={form.paper_number}
              onChange={(e) => setForm((f) => ({ ...f, paper_number: Number(e.target.value) }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Session (optional)</label>
            <select
              value={form.exam_session}
              onChange={(e) => setForm((f) => ({ ...f, exam_session: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">None</option>
              {SESSIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Duration (mins)</label>
            <input
              type="number"
              min={30}
              max={360}
              value={form.duration_minutes}
              onChange={(e) => setForm((f) => ({ ...f, duration_minutes: Number(e.target.value) }))}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="col-span-2 space-y-1.5">
            <label className="text-xs font-medium text-foreground">PDF file</label>
            <input
              required
              ref={fileRef}
              type="file"
              accept=".pdf,application/pdf"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring file:mr-3 file:text-xs file:font-medium file:border-0 file:bg-primary/10 file:text-primary file:rounded file:px-2 file:py-1"
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60"
        >
          {submitting ? "Uploading…" : "Upload & extract"}
        </button>
      </form>
    </div>
  );
}
