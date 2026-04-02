"use client";

import { useEffect, useRef, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Subject = { id: string; name: string; level: string };
type Paper = {
  id: string;
  subject_name: string;
  year: number;
  paper_number: number;
  duration_minutes: number;
  status: string;
  created_at: string;
};

const LEVELS = ["Grade7", "O", "A"] as const;
type Level = (typeof LEVELS)[number];

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    processing: "bg-yellow-100 text-yellow-800 border-yellow-200",
    ready: "bg-green-100 text-green-800 border-green-200",
    error: "bg-red-100 text-red-800 border-red-200",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
        colors[status] ?? "bg-gray-100 text-gray-700 border-gray-200"
      }`}
    >
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

  // Subject selection: "existing" or "new"
  const [subjectMode, setSubjectMode] = useState<"existing" | "new">("existing");
  const [subjectId, setSubjectId] = useState("");
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newSubjectLevel, setNewSubjectLevel] = useState<Level>("O");

  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [paperNumber, setPaperNumber] = useState("1");
  const [durationMinutes, setDurationMinutes] = useState("120");
  const [file, setFile] = useState<File | null>(null);
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
    fetch(`${supabaseUrl}/rest/v1/subject?select=id,name,level&order=name`, {
      headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
    })
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setSubjects(data); })
      .catch(() => {});
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !year || !paperNumber || !durationMinutes) return;

    if (subjectMode === "existing" && !subjectId) {
      setUploadError("Please select a subject, or switch to 'New subject' to create one.");
      return;
    }
    if (subjectMode === "new" && !newSubjectName.trim()) {
      setUploadError("Please enter a subject name.");
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
    }
    form.append("year", year);
    form.append("paper_number", paperNumber);
    form.append("duration_minutes", durationMinutes);
    form.append("file", file);

    try {
      const res = await fetch(`${BACKEND}/admin/papers/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Upload failed (${res.status})`);
      }
      setUploadSuccess(true);
      setFile(null);
      setYear(String(new Date().getFullYear()));
      setPaperNumber("1");
      setDurationMinutes("120");
      setSubjectId("");
      setNewSubjectName("");
      if (fileRef.current) fileRef.current.value = "";
      loadPapers();
      loadSubjects(); // refresh in case a new subject was created
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-10">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Paper Management</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Upload past papers and review extracted questions
          </p>
        </div>

        {/* Upload form */}
        <div className="bg-card border border-border rounded-2xl p-6">
          <h2 className="text-base font-semibold text-foreground mb-5">Upload New Paper</h2>
          <form onSubmit={handleUpload} className="space-y-5">

            {/* Subject */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-sm font-medium text-foreground">Subject</label>
                <button
                  type="button"
                  onClick={() => {
                    setSubjectMode((m) => (m === "existing" ? "new" : "existing"));
                    setUploadError(null);
                  }}
                  className="text-xs text-primary hover:underline"
                >
                  {subjectMode === "existing"
                    ? subjects.length === 0
                      ? "No subjects yet — create one"
                      : "+ New subject"
                    : "← Pick existing subject"}
                </button>
              </div>

              {subjectMode === "existing" ? (
                <select
                  value={subjectId}
                  onChange={(e) => setSubjectId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">
                    {subjects.length === 0 ? 'No subjects — click "+ New subject" above' : "Select subject…"}
                  </option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.level})
                    </option>
                  ))}
                </select>
              ) : (
                <div className="flex gap-3">
                  <input
                    type="text"
                    placeholder="e.g. Mathematics, Combined Science"
                    value={newSubjectName}
                    onChange={(e) => setNewSubjectName(e.target.value)}
                    className="flex-1 px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <select
                    value={newSubjectLevel}
                    onChange={(e) => setNewSubjectLevel(e.target.value as Level)}
                    className="px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {LEVELS.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Paper Number
                </label>
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
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Duration (minutes)
                </label>
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

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">PDF File</label>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,application/pdf"
                required
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full px-3.5 py-2 rounded-lg border border-border bg-background text-foreground text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:font-medium file:bg-primary file:text-primary-foreground hover:file:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {uploadError && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">
                {uploadError}
              </p>
            )}
            {uploadSuccess && (
              <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3.5 py-2.5">
                Paper uploaded — extraction is running in the background. Refresh in ~30 seconds to see the status.
              </p>
            )}

            <button
              type="submit"
              disabled={uploading}
              className="px-5 py-2.5 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? "Uploading…" : "Upload & Extract"}
            </button>
          </form>
        </div>

        {/* Papers list */}
        <div className="bg-card border border-border rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-foreground">Uploaded Papers</h2>
            <button
              onClick={loadPapers}
              className="text-xs text-muted-foreground hover:text-foreground transition"
            >
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
                    <th className="pb-3 pr-4 font-medium">Paper</th>
                    <th className="pb-3 pr-4 font-medium">Duration</th>
                    <th className="pb-3 pr-4 font-medium">Status</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {papers.map((p) => (
                    <tr key={p.id} className="align-middle">
                      <td className="py-3 pr-4 text-foreground font-medium">
                        {p.subject_name}
                      </td>
                      <td className="py-3 pr-4 text-foreground">{p.year}</td>
                      <td className="py-3 pr-4 text-foreground">{p.paper_number}</td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {p.duration_minutes ? formatDuration(p.duration_minutes) : "—"}
                      </td>
                      <td className="py-3 pr-4">
                        <StatusBadge status={p.status} />
                      </td>
                      <td className="py-3">
                        {p.status === "ready" ? (
                          <a
                            href={`/admin/papers/${p.id}/questions`}
                            className="text-primary text-xs font-medium hover:underline"
                          >
                            Review Questions →
                          </a>
                        ) : p.status === "processing" ? (
                          <span className="text-muted-foreground text-xs">Extracting…</span>
                        ) : (
                          <span className="text-red-600 text-xs">Extraction failed</span>
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
    </div>
  );
}
