"use client";

import { useEffect, useState, useRef } from "react";
import { adminListSubjects, adminUploadSyllabus, AdminSubject } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { CheckCircle, FileUp, AlertCircle } from "lucide-react";

export default function SyllabusUploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [subjects, setSubjects] = useState<AdminSubject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);

  const [subjectId, setSubjectId] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ chunks_inserted: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminListSubjects()
      .then(setSubjects)
      .catch(() => {})
      .finally(() => setSubjectsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectId || !file) {
      setError("All fields are required.");
      return;
    }

    const formData = new FormData();
    formData.append("subject_id", subjectId);
    formData.append("file", file);

    setUploading(true);
    setError(null);
    try {
      const res = await adminUploadSyllabus(formData);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (result) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto">
          <CheckCircle className="w-8 h-8 text-emerald-500" />
        </div>
        <h2 className="text-xl font-bold text-zinc-900">Syllabus uploaded</h2>
        <p className="text-zinc-500 text-sm">
          <strong>{result.chunks_inserted}</strong> topic chunk{result.chunks_inserted !== 1 ? "s" : ""} extracted and saved.
        </p>
        <Button
          variant="outline"
          onClick={() => {
            setResult(null);
            setFile(null);
            setSubjectId("");
          }}
        >
          Upload Another
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Upload Syllabus</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Upload a ZIMSEC syllabus PDF — topics will be extracted and used to improve AI marking.
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
        </div>

        {/* File */}
        <div className="space-y-1.5">
          <Label>Syllabus PDF</Label>
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

        <Button type="submit" disabled={uploading || !file || !subjectId} className="w-full">
          {uploading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Uploading…
            </>
          ) : (
            "Upload & Parse Syllabus"
          )}
        </Button>
      </form>
    </div>
  );
}
