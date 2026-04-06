"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function deletePaper(paperId: string): Promise<void> {
  const res = await fetch(`${BACKEND}/admin/papers/${paperId}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Delete failed (${res.status})`);
  }
}

type Subject = { id: string; name: string; level: string; exam_board?: string };
type Paper = {
  id: string;
  subject_name: string;
  year: number;
  paper_number: number;
  exam_session: "june" | "november" | null;
  duration_minutes: number;
  status: string;
  created_at: string;
};

type ExamBoard = "zimsec" | "cambridge";

const ZIMSEC_LEVELS = ["Grade7", "O", "A"] as const;
const CAMBRIDGE_LEVELS = ["IGCSE", "AS_Level", "A_Level"] as const;

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
  IGCSE: "Cambridge IGCSE",
  AS_Level: "Cambridge AS Level",
  A_Level: "Cambridge A Level",
};

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    processing: "bg-yellow-100 text-yellow-800 border-yellow-200",
    ready: "bg-green-100 text-green-800 border-green-200",
    error: "bg-red-100 text-red-800 border-red-200",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors[status] ?? "bg-gray-100 text-gray-700 border-gray-200"}`}>
      {status}
    </span>
  );
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export default function AdminPapersPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [examBoard, setExamBoard] = useState<ExamBoard>("zimsec");
  const [subjectMode, setSubjectMode] = useState<"existing" | "new">("existing");
  const [subjectId, setSubjectId] = useState("");
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newSubjectLevel, setNewSubjectLevel] = useState("O");

  const levels = examBoard === "cambridge" ? CAMBRIDGE_LEVELS : ZIMSEC_LEVELS;
  const filteredSubjects = subjects.filter(
    (s) => !s.exam_board || s.exam_board === examBoard
  );

  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [paperNumber, setPaperNumber] = useState("1");
  const [examSession, setExamSession] = useState<"june" | "november">("november");
  const [durationMinutes, setDurationMinutes] = useState("120");

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPapers();
    loadSubjects();
  }, []);

  function loadPapers() {
    fetch(`${BACKEND}/admin/papers`)
      .then((r) => r.json())
      .then((data) => setPapers(Array.isArray(data) ? data : []))
      .catch(() => {});
  }

  function loadSubjects() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!supabaseUrl || !anonKey) return;
    fetch(`${supabaseUrl}/rest/v1/subject?select=id,name,level,exam_board&order=name`, {
      headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
    })
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setSubjects(data); })
      .catch(() => {});
  }

  const acceptFile = useCallback((f: File) => {
    if (f.type !== "application/pdf" && !f.name.endsWith(".pdf")) {
      setUploadError("Only PDF files are accepted.");
      return;
    }
    setFile(f);
    setUploadError(null);
    setUploadSuccess(false);
  }, []);

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function onDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) acceptFile(dropped);
  }

  function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    if (picked) acceptFile(picked);
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;

    if (subjectMode === "existing" && !subjectId) {
      setUploadError("Select a subject, or switch to 'New subject'.");
      return;
    }
    if (subjectMode === "new" && !newSubjectName.trim()) {
      setUploadError("Enter a subject name.");
      return;
    }

    setUploadError(null);
    setUploadSuccess(false);
    setUploading(true);

    const form = new FormData();
    if (subjectMode === "existing") {
      form.append("subject_id", subjectId);
    } else {
      form.append("subject_name", newSubjectName.trim());
      form.append("level", newSubjectLevel);
      form.append("exam_board", examBoard);
    }
    form.append("year", year);
    form.append("paper_number", paperNumber);
    form.append("exam_session", examSession);
    form.append("duration_minutes", durationMinutes);
    form.append("file", file);

    try {
      const res = await fetch(`${BACKEND}/admin/papers/upload`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Upload failed (${res.status})`);
      }
      setUploadSuccess(true);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      loadPapers();
      loadSubjects();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(paperId: string) {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deletePaper(paperId);
      setConfirmDeleteId(null);
      loadPapers();
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <>
    <div className="max-w-4xl space-y-8">

        {/* Header */}
        <div>
          <h1 className="text-xl font-semibold text-foreground">Paper Management</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Upload past papers and review extracted questions</p>
        </div>

        {/* Upload form */}
        <form onSubmit={handleUpload} className="bg-card border border-border rounded-2xl p-6 space-y-5">
          <h2 className="text-base font-semibold text-foreground">Upload New Paper</h2>

          {/* Exam board toggle */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Exam Board</label>
            <div className="inline-flex rounded-lg border border-border bg-muted/30 p-1 gap-1">
              <button
                type="button"
                onClick={() => { setExamBoard("zimsec"); setSubjectId(""); setNewSubjectLevel("O"); }}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${examBoard === "zimsec" ? "bg-white shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                🇿🇼 ZIMSEC
              </button>
              <button
                type="button"
                onClick={() => { setExamBoard("cambridge"); setSubjectId(""); setNewSubjectLevel("IGCSE"); }}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${examBoard === "cambridge" ? "bg-white shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                🎓 Cambridge
              </button>
            </div>
          </div>

          {/* Drop zone */}
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed cursor-pointer transition-colors py-10 px-6
              ${dragging ? "border-primary bg-primary/5" : file ? "border-green-400 bg-green-50" : "border-border hover:border-primary/50 hover:bg-muted/40"}`}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={onFileInput}
            />

            {file ? (
              <>
                <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null); if (fileRef.current) fileRef.current.value = ""; }}
                  className="text-xs text-red-500 hover:underline mt-1"
                >
                  Remove
                </button>
              </>
            ) : (
              <>
                <svg className="w-8 h-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <p className="text-sm font-medium text-foreground">
                  {dragging ? "Drop the PDF here" : "Drag & drop a PDF, or click to browse"}
                </p>
                <p className="text-xs text-muted-foreground">PDF files only</p>
              </>
            )}
          </div>

          {/* Subject */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-medium text-foreground">Subject</label>
              <button
                type="button"
                onClick={() => { setSubjectMode((m) => (m === "existing" ? "new" : "existing")); setUploadError(null); }}
                className="text-xs text-primary hover:underline"
              >
                {subjectMode === "existing" ? (subjects.length === 0 ? "No subjects yet — create one" : "+ New subject") : "← Pick existing"}
              </button>
            </div>

            {subjectMode === "existing" ? (
              <select
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">{filteredSubjects.length === 0 ? `No ${examBoard === "cambridge" ? "Cambridge" : "ZIMSEC"} subjects yet — create one` : "Select subject…"}</option>
                {filteredSubjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({LEVEL_LABELS[s.level] ?? s.level})</option>
                ))}
              </select>
            ) : (
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="e.g. Mathematics"
                  value={newSubjectName}
                  onChange={(e) => setNewSubjectName(e.target.value)}
                  className="flex-1 px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <select
                  value={newSubjectLevel}
                  onChange={(e) => setNewSubjectLevel(e.target.value)}
                  className="px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {levels.map((l) => <option key={l} value={l}>{LEVEL_LABELS[l]}</option>)}
                </select>
              </div>
            )}
          </div>

          {/* Year / Session / Paper / Duration */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Year</label>
              <input
                type="number"
                required
                min={1990}
                max={2035}
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Session</label>
              <div className="inline-flex w-full rounded-lg border border-border bg-muted/30 p-1 gap-1">
                {(["june", "november"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setExamSession(s)}
                    className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-all capitalize ${examSession === s ? "bg-white shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    {s === "june" ? "June" : "Nov"}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Paper Number</label>
              <input
                type="number"
                required
                min={1}
                max={4}
                value={paperNumber}
                onChange={(e) => setPaperNumber(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Duration</label>
              <select
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="90">90 min (1.5 hrs)</option>
                <option value="120">120 min (2 hrs)</option>
                <option value="150">150 min (2.5 hrs)</option>
                <option value="180">180 min (3 hrs)</option>
              </select>
            </div>
          </div>

          {uploadError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">{uploadError}</p>
          )}
          {uploadSuccess && (
            <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3.5 py-2.5">
              Paper uploaded — extraction running in background. Refresh in ~30s to see status.
            </p>
          )}

          <button
            type="submit"
            disabled={uploading || !file}
            className="w-full py-2.5 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Uploading…
              </span>
            ) : "Upload & Extract"}
          </button>
        </form>

        {/* Papers list */}
        <div className="bg-card border border-border rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-foreground">Uploaded Papers</h2>
            <button onClick={loadPapers} className="text-xs text-muted-foreground hover:text-foreground transition">
              Refresh
            </button>
          </div>

          {papers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No papers uploaded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground border-b border-border">
                    <th className="pb-3 pr-4 font-medium">Subject</th>
                    <th className="pb-3 pr-4 font-medium">Year</th>
                    <th className="pb-3 pr-4 font-medium">Session</th>
                    <th className="pb-3 pr-4 font-medium">Paper</th>
                    <th className="pb-3 pr-4 font-medium">Duration</th>
                    <th className="pb-3 pr-4 font-medium">Status</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {papers.map((p) => (
                    <tr key={p.id} className="align-middle">
                      <td className="py-3 pr-4 font-medium text-foreground">{p.subject_name}</td>
                      <td className="py-3 pr-4 text-foreground">{p.year}</td>
                      <td className="py-3 pr-4 text-foreground capitalize">{p.exam_session ?? "—"}</td>
                      <td className="py-3 pr-4 text-foreground">{p.paper_number}</td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {p.duration_minutes ? formatDuration(p.duration_minutes) : "—"}
                      </td>
                      <td className="py-3 pr-4"><StatusBadge status={p.status} /></td>
                      <td className="py-3">
                        <div className="flex items-center gap-3">
                          {p.status === "ready" ? (
                            <a href={`/admin/papers/${p.id}/questions`} className="text-primary text-xs font-medium hover:underline">
                              Review Questions →
                            </a>
                          ) : p.status === "processing" ? (
                            <span className="text-muted-foreground text-xs">Extracting…</span>
                          ) : (
                            <span className="text-red-600 text-xs">Extraction failed</span>
                          )}
                          <button
                            onClick={() => { setConfirmDeleteId(p.id); setDeleteError(null); }}
                            className="text-red-400 hover:text-red-600 transition"
                            title="Delete paper"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      {/* Delete confirmation modal */}
      {confirmDeleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-card border border-border rounded-2xl p-6 w-full max-w-sm shadow-xl mx-4">
            <h3 className="text-base font-semibold text-foreground mb-2">Delete paper?</h3>
            <p className="text-sm text-muted-foreground mb-5">
              This will permanently delete the paper, all its extracted questions, and the PDF from storage. This cannot be undone.
            </p>
            {deleteError && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">{deleteError}</p>
            )}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => { setConfirmDeleteId(null); setDeleteError(null); }}
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-foreground border border-border rounded-lg hover:bg-muted/40 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteId)}
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition disabled:opacity-50 flex items-center gap-2"
              >
                {deleting && (
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                )}
                {deleting ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}
