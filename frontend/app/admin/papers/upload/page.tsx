"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { adminListSubjects, adminUploadPaper, AdminSubject } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle, FileUp, AlertCircle } from "lucide-react";

export default function UploadPaperPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [subjects, setSubjects] = useState<AdminSubject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);

  const [subjectId, setSubjectId] = useState("");
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [paperNumber, setPaperNumber] = useState("1");
  const [file, setFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState<{ paper_id: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminListSubjects()
      .then(setSubjects)
      .catch(() => {})
      .finally(() => setSubjectsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectId || !year || !paperNumber || !file) {
      setError("All fields are required.");
      return;
    }

    const formData = new FormData();
    formData.append("subject_id", subjectId);
    formData.append("year", year);
    formData.append("paper_number", paperNumber);
    formData.append("file", file);

    setUploading(true);
    setError(null);
    try {
      const res = await adminUploadPaper(formData);
      setSuccess({ paper_id: res.paper_id });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto">
          <CheckCircle className="w-8 h-8 text-emerald-500" />
        </div>
        <h2 className="text-xl font-bold text-zinc-900">Paper uploaded</h2>
        <p className="text-zinc-500 text-sm">
          Question extraction is running in the background. The paper will appear in the list with
          status <strong>Processing</strong>. Refresh the papers list to check progress.
        </p>
        <div className="flex gap-3 justify-center pt-2">
          <Button variant="outline" onClick={() => router.push("/admin/papers")}>
            View Papers
          </Button>
          <Button onClick={() => router.push(`/admin/papers/${success.paper_id}`)}>
            Go to QA Review
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Upload Past Paper</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Upload a PDF — questions will be extracted automatically by AI.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-zinc-200 rounded-xl p-6 space-y-5">
        {/* Subject */}
        <div className="space-y-1.5">
          <Label htmlFor="subject">Subject</Label>
          {subjectsLoading ? (
            <div className="h-9 bg-zinc-50 rounded-md border border-zinc-200 animate-pulse" />
          ) : (
            <select
              id="subject"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="w-full h-9 rounded-md border border-zinc-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
              required
            >
              <option value="">Select a subject…</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.level})
                </option>
              ))}
            </select>
          )}
          {subjects.length === 0 && !subjectsLoading && (
            <p className="text-xs text-amber-600">
              No subjects found. Add subjects to the database first.
            </p>
          )}
        </div>

        {/* Year */}
        <div className="space-y-1.5">
          <Label htmlFor="year">Year</Label>
          <Input
            id="year"
            type="number"
            min={2000}
            max={new Date().getFullYear()}
            value={year}
            onChange={(e) => setYear(e.target.value)}
            required
          />
        </div>

        {/* Paper number */}
        <div className="space-y-1.5">
          <Label htmlFor="paper_number">Paper Number</Label>
          <select
            id="paper_number"
            value={paperNumber}
            onChange={(e) => setPaperNumber(e.target.value)}
            className="w-full h-9 rounded-md border border-zinc-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
          >
            <option value="1">Paper 1</option>
            <option value="2">Paper 2</option>
            <option value="3">Paper 3</option>
          </select>
        </div>

        {/* File */}
        <div className="space-y-1.5">
          <Label>PDF File</Label>
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              file ? "border-emerald-300 bg-emerald-50" : "border-zinc-300 hover:border-zinc-400 hover:bg-zinc-50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <FileUp className={`w-8 h-8 mx-auto mb-2 ${file ? "text-emerald-500" : "text-zinc-400"}`} />
            {file ? (
              <div>
                <p className="font-medium text-emerald-700 text-sm">{file.name}</p>
                <p className="text-xs text-emerald-600 mt-0.5">
                  {(file.size / 1024 / 1024).toFixed(1)} MB — click to change
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm text-zinc-600">Click to select PDF</p>
                <p className="text-xs text-zinc-400 mt-0.5">PDF files only</p>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        <Button type="submit" disabled={uploading || !file} className="w-full">
          {uploading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Uploading…
            </>
          ) : (
            "Upload & Extract Questions"
          )}
        </Button>
      </form>
    </div>
  );
}
