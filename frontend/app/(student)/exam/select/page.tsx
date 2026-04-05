"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getSubjects,
  getPapersForSubject,
  createSession,
  type Subject,
  type Paper,
} from "@/lib/api";
import { useStudent } from "@/lib/student-context";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { cn } from "@/lib/utils";

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
  IGCSE: "Cambridge IGCSE",
  AS_Level: "Cambridge AS Level",
  A_Level: "Cambridge A Level",
};

export default function ExamSelectPage() {
  const router = useRouter();
  const { id: studentId, examBoard, level } = useStudent();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [mode, setMode] = useState<"exam" | "practice">("exam");
  const [loading, setLoading] = useState(true);
  const [papersLoading, setPapersLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load subjects filtered to the student's board + level (from context)
  useEffect(() => {
    setLoading(true);
    getSubjects(examBoard || undefined, level || undefined)
      .then(setSubjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [examBoard, level]);

  async function handleSelectSubject(subject: Subject) {
    setSelectedSubject(subject);
    setSelectedPaper(null);
    setPapersLoading(true);
    setError(null);
    try {
      const data = await getPapersForSubject(subject.id);
      setPapers(data);
      setStep(2);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPapersLoading(false);
    }
  }

  async function handleConfirm() {
    if (!studentId) {
      setError("Could not identify your account — please sign in again.");
      return;
    }
    if (!selectedPaper) return;

    setConfirming(true);
    setError(null);
    try {
      const { session_id } = await createSession(studentId, selectedPaper.id, mode);
      router.push(`/exam/${session_id}`);
    } catch (e) {
      setError((e as Error).message);
      setConfirming(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (error && step === 1) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12">
        <ErrorState
          error={error}
          onRetry={() => {
            setError(null);
            setLoading(true);
            getSubjects(examBoard || undefined, level || undefined)
              .then(setSubjects)
              .catch((e) => setError(e.message))
              .finally(() => setLoading(false));
          }}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {(["Subject", "Paper", "Confirm"] as const).map((label, i) => (
          <span
            key={label}
            className={cn(
              "px-2 py-0.5 rounded",
              step === i + 1
                ? "bg-primary text-primary-foreground font-medium"
                : "text-muted-foreground"
            )}
          >
            {i + 1}. {label}
          </span>
        ))}
      </div>

      {/* Step 1 — Subject selection */}
      {step === 1 && (
        <div className="space-y-3">
          <h1 className="text-xl font-semibold">Choose a subject</h1>
          {subjects.length === 0 ? (
            <EmptyState
              title="No papers available yet"
              description="Check back soon — papers are being added."
            />
          ) : (
            <div className="grid gap-3">
              {subjects.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelectSubject(s)}
                  disabled={papersLoading}
                  className="text-left w-full"
                >
                  <Card className="hover:border-primary transition-colors cursor-pointer">
                    <CardContent className="flex items-center justify-between py-4 px-5">
                      <div>
                        <p className="font-medium text-foreground">{s.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {s.paper_count} paper{s.paper_count !== 1 ? "s" : ""} available
                        </p>
                      </div>
                      <Badge variant="secondary">
                        {LEVEL_LABELS[s.level] ?? s.level}
                      </Badge>
                    </CardContent>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 2 — Paper selection */}
      {step === 2 && selectedSubject && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setStep(1)}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back
            </button>
            <h1 className="text-xl font-semibold">{selectedSubject.name}</h1>
          </div>
          {papersLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 rounded-lg bg-muted" />
              ))}
            </div>
          ) : papers.length === 0 ? (
            <EmptyState
              title="No papers available for this subject"
              description="Try a different subject."
            />
          ) : (
            <div className="grid gap-2">
              {papers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setSelectedPaper(p);
                    setStep(3);
                  }}
                  className="text-left w-full"
                >
                  <Card className="hover:border-primary transition-colors cursor-pointer">
                    <CardContent className="flex items-center justify-between py-3 px-5">
                      <span className="font-medium text-foreground">
                        {p.year} — Paper {p.paper_number}
                      </span>
                      <span className="text-sm text-muted-foreground">→</span>
                    </CardContent>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 3 — Confirm */}
      {step === 3 && selectedSubject && selectedPaper && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setStep(2)}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back
            </button>
            <h1 className="text-xl font-semibold">Confirm your session</h1>
          </div>

          <Card>
            <CardContent className="py-4 px-5 space-y-1">
              <p className="font-medium text-foreground">{selectedSubject.name}</p>
              <p className="text-sm text-muted-foreground">
                {selectedPaper.year} — Paper {selectedPaper.paper_number}
              </p>
            </CardContent>
          </Card>

          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Session mode</p>
            <div className="grid grid-cols-2 gap-3">
              {(["exam", "practice"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    "border rounded-lg p-4 text-left transition-colors",
                    mode === m
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  <p className="font-medium text-foreground capitalize">{m} Mode</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {m === "exam"
                      ? "Timed, full submission at end"
                      : "Instant feedback per question"}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <Button
            onClick={handleConfirm}
            disabled={confirming}
            size="lg"
            className="w-full"
          >
            {confirming ? "Starting session..." : "Start Session"}
          </Button>
        </div>
      )}
    </div>
  );
}
