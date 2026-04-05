"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  getSubjects, getPracticeSession, getNextQuestion, getSubjectTopics,
  getWeakTopics, submitAttempt, flagAttempt, getPapersForSubject,
  type Subject, type Question, type PracticeAttemptResult, type WeakTopic,
} from "@/lib/api";
import { UpgradePrompt } from "@/components/UpgradePrompt";
import { useQuota } from "@/hooks/useQuota";
import { MathText } from "@/components/math-text";
import { cn } from "@/lib/utils";
import { useStudent } from "@/lib/student-context";

// ── Constants ──────────────────────────────────────────────────────────────────

const MCQ_OPTIONS = ["A", "B", "C", "D"] as const;
const OPTION_COLORS = {
  A: { base: "border-blue-200   bg-blue-50/50   hover:border-blue-400",   selected: "border-blue-500   bg-blue-100",   badge: "bg-blue-500"   },
  B: { base: "border-green-200  bg-green-50/50  hover:border-green-400",  selected: "border-green-500  bg-green-100",  badge: "bg-green-500"  },
  C: { base: "border-amber-200  bg-amber-50/50  hover:border-amber-400",  selected: "border-amber-500  bg-amber-100",  badge: "bg-amber-500"  },
  D: { base: "border-rose-200   bg-rose-50/50   hover:border-rose-400",   selected: "border-rose-500   bg-rose-100",   badge: "bg-rose-500"   },
};
const LEVEL_COLORS: Record<string, string> = {
  Grade7: "bg-sky-100   text-sky-700   border-sky-200",
  O:      "bg-green-100 text-green-700 border-green-200",
  A:      "bg-purple-100 text-purple-700 border-purple-200",
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function groupByLevel(subjects: Subject[]) {
  return subjects.reduce<Record<string, Subject[]>>((acc, s) => {
    (acc[s.level] ??= []).push(s);
    return acc;
  }, {});
}

async function uploadAnswerImage(file: File, sessionId: string): Promise<string> {
  const supabase = createClient();
  const ext = file.name.split(".").pop() ?? "jpg";
  const path = `${sessionId}/${Date.now()}.${ext}`;
  const { error } = await supabase.storage.from("answer-images").upload(path, file, { upsert: true });
  if (error) throw new Error(error.message);
  return supabase.storage.from("answer-images").getPublicUrl(path).data.publicUrl;
}

// ── Feedback card ──────────────────────────────────────────────────────────────

function FeedbackCard({ result, question, onNext, onFlag, flagged }: {
  result: PracticeAttemptResult;
  question: Question;
  onNext: () => void;
  onFlag: () => void;
  flagged: boolean;
}) {
  const score = result.ai_score ?? 0;
  const pct = question.marks > 0 ? score / question.marks : 0;
  const isGood = pct >= 0.7;
  const isPerfect = pct >= 1;
  const msg = isPerfect ? "Perfect! 🎉" : pct >= 0.7 ? "Well done! ✓" : pct >= 0.4 ? "Getting there 📖" : "Keep going 💪";
  const xp = score * 10;

  return (
    <div className={cn(
      "rounded-2xl border-2 p-5 space-y-4 animate-in slide-in-from-bottom-4 duration-300",
      isGood ? "border-green-300 bg-green-50" : "border-red-200 bg-red-50/50"
    )}>
      <div className="flex items-center justify-between">
        <p className={cn("font-bold text-lg", isGood ? "text-green-700" : "text-red-700")}>{msg}</p>
        <div className="flex items-center gap-2">
          {xp > 0 && (
            <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
              +{xp} XP
            </span>
          )}
          <span className={cn(
            "font-bold text-sm px-3 py-1 rounded-full border",
            isGood ? "bg-green-100 text-green-700 border-green-200" : "bg-red-100 text-red-700 border-red-200"
          )}>
            {score}/{question.marks}
          </span>
        </div>
      </div>

      {result.ai_feedback && (
        <div className="space-y-3 text-sm">
          {result.ai_feedback.correct_points.length > 0 && (
            <div>
              <p className="font-semibold text-green-700 mb-1.5">✓ Correct</p>
              <ul className="space-y-1 pl-3 border-l-2 border-green-300 text-muted-foreground">
                {result.ai_feedback.correct_points.map((p, i) => (
                  <li key={i}><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.missing_points.length > 0 && (
            <div>
              <p className="font-semibold text-red-700 mb-1.5">✗ Missing</p>
              <ul className="space-y-1 pl-3 border-l-2 border-red-300 text-muted-foreground">
                {result.ai_feedback.missing_points.map((p, i) => (
                  <li key={i}><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.examiner_note && (
            <div className="bg-white/70 border border-border rounded-xl px-4 py-3">
              <p className="font-semibold text-foreground mb-0.5">Examiner note</p>
              <MathText text={result.ai_feedback.examiner_note} className="text-muted-foreground" />
            </div>
          )}
        </div>
      )}

      {result.ai_references && result.ai_references.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {result.ai_references.map((r, i) => (
            <span key={i} className="text-xs px-2.5 py-0.5 rounded-full bg-white border border-border text-muted-foreground">
              {r}
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-3 pt-1">
        <button
          onClick={onNext}
          className="flex-1 py-3 bg-primary text-primary-foreground rounded-xl font-bold text-sm hover:opacity-90 transition"
        >
          Next Question →
        </button>
        <button
          onClick={onFlag}
          disabled={flagged}
          className="px-4 py-3 border border-border rounded-xl text-xs text-muted-foreground hover:bg-muted disabled:opacity-40 transition"
        >
          {flagged ? "Flagged" : "Flag"}
        </button>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function PracticePage() {
  const { guardedSubmit, showUpgrade, upgradeDetail, dismissUpgrade } = useQuota();
  const { id: studentId, examBoard, level } = useStudent();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);

  const [stage, setStage] = useState<"selecting" | "paper-select" | "practicing">("selecting");
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [availablePaperNumbers, setAvailablePaperNumbers] = useState<number[]>([]);
  const [selectedPaperNumber, setSelectedPaperNumber] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [answerTab, setAnswerTab] = useState<"text" | "photo">("text");
  const [answerImageUrl, setAnswerImageUrl] = useState<string | null>(null);
  const [result, setResult] = useState<PracticeAttemptResult | null>(null);
  const [weakTopics, setWeakTopics] = useState<WeakTopic[]>([]);
  const [imageUploading, setImageUploading] = useState(false);

  // Stats
  const [doneCount, setDoneCount] = useState(0);
  const [correctTotal, setCorrectTotal] = useState(0);
  const [maxTotal, setMaxTotal] = useState(0);
  const [streak, setStreak] = useState(0);
  const [xp, setXp] = useState(0);

  const [questionLoading, setQuestionLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flagged, setFlagged] = useState(false);
  const imageRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getSubjects(examBoard || undefined, level || undefined)
      .then(setSubjects)
      .catch(() => setError("Failed to load subjects"))
      .finally(() => setSubjectsLoading(false));
  }, [examBoard, level]);

  const refreshWeakTopics = useCallback(() => {
    if (!selectedSubject || !studentId) return;
    getWeakTopics(selectedSubject.id, studentId).then(setWeakTopics).catch(() => {});
  }, [selectedSubject, studentId]);

  const fetchNextQuestion = useCallback(async (topic: string | null) => {
    if (!selectedSubject || !studentId) return;
    setQuestionLoading(true);
    setResult(null);
    setAnswer("");
    setAnswerImageUrl(null);
    setAnswerTab("text");
    setFlagged(false);
    setError(null);
    try {
      const q = await getNextQuestion(selectedSubject.id, studentId, topic ?? undefined, selectedPaperNumber ?? undefined);
      setQuestion(q);
    } catch {
      setError("No more questions for this filter.");
      setQuestion(null);
    } finally {
      setQuestionLoading(false);
    }
  }, [selectedSubject, studentId, selectedPaperNumber]);

  async function selectSubject(subject: Subject) {
    if (!studentId) return;
    setError(null);
    setSelectedSubject(subject);
    setAvailablePaperNumbers([]);
    setSelectedPaperNumber(null);
    try {
      const papers = await getPapersForSubject(subject.id);
      const nums = [...new Set(papers.map((p) => p.paper_number))].sort((a, b) => a - b);
      setAvailablePaperNumbers(nums);
      setStage("paper-select");
    } catch {
      setError("Failed to load papers.");
    }
  }

  async function startPractice(paperNumber: number | null) {
    if (!studentId || !selectedSubject) return;
    setError(null);
    setSelectedPaperNumber(paperNumber);
    setStage("practicing");
    setDoneCount(0); setCorrectTotal(0); setMaxTotal(0); setStreak(0); setXp(0);
    setActiveTopic(null);
    try {
      const [sessionRes, topicList] = await Promise.all([
        getPracticeSession(studentId, selectedSubject.id),
        getSubjectTopics(selectedSubject.id),
      ]);
      setSessionId(sessionRes.session_id);
      setTopics(topicList);
      setQuestionLoading(true);
      const q = await getNextQuestion(selectedSubject.id, studentId, undefined, paperNumber ?? undefined);
      setQuestion(q);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start");
    } finally {
      setQuestionLoading(false);
    }
  }

  async function handleSubmit() {
    if (!sessionId || !question) return;
    if (!answer.trim() && !answerImageUrl) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await guardedSubmit(() =>
        submitAttempt(sessionId, question.id, answer.trim(), answerImageUrl ?? undefined)
      );
      if (!res) return;
      setResult(res);
      setDoneCount((n) => n + 1);
      const score = res.ai_score ?? 0;
      setCorrectTotal((n) => n + score);
      setMaxTotal((n) => n + question.marks);
      setStreak((s) => (score > 0 ? s + 1 : 0));
      setXp((n) => n + score * 10);
      refreshWeakTopics();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFlag() {
    if (!result) return;
    try { await flagAttempt(result.id); setFlagged(true); } catch {}
  }

  async function handleImageFile(file: File) {
    if (!sessionId) return;
    setImageUploading(true);
    try {
      const url = await uploadAnswerImage(file, sessionId);
      setAnswerImageUrl(url);
    } catch {
      setError("Image upload failed.");
    } finally {
      setImageUploading(false);
    }
  }

  const accuracy = maxTotal > 0 ? Math.round((correctTotal / maxTotal) * 100) : null;
  const upgradeOverlay = showUpgrade && upgradeDetail && (
    <UpgradePrompt detail={upgradeDetail} onDismiss={dismissUpgrade} />
  );

  // ── Paper selection ──────────────────────────────────────────────────────────

  if (stage === "paper-select" && selectedSubject) {
    const PAPER_LABELS: Record<number, string> = {
      1: "Paper 1 — Multiple Choice",
      2: "Paper 2 — Structured / Theory",
      3: "Paper 3 — Practical / Extended",
      4: "Paper 4 — Advanced Theory",
    };

    return (
      <div className="max-w-2xl mx-auto px-4 py-10 space-y-8">
        {upgradeOverlay}
        <div className="flex items-center gap-3">
          <button
            onClick={() => { setStage("selecting"); setSelectedSubject(null); }}
            className="text-muted-foreground hover:text-foreground transition text-sm"
          >
            ←
          </button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{selectedSubject.name}</h1>
            <p className="text-muted-foreground text-sm mt-0.5">Choose a paper to practise</p>
          </div>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {availablePaperNumbers.map((num) => (
            <button
              key={num}
              onClick={() => startPractice(num)}
              className="text-left border border-border rounded-xl px-5 py-4 bg-card hover:border-primary/40 hover:bg-primary/5 hover:shadow-sm transition-all group"
            >
              <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
                Paper {num}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {PAPER_LABELS[num] ?? `Paper ${num} questions`}
              </p>
            </button>
          ))}
          <button
            onClick={() => startPractice(null)}
            className="text-left border border-border rounded-xl px-5 py-4 bg-card hover:border-primary/40 hover:bg-primary/5 hover:shadow-sm transition-all group sm:col-span-2"
          >
            <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
              All Papers
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Adaptive practice across all paper types
            </p>
          </button>
        </div>
      </div>
    );
  }

  // ── Subject selection ────────────────────────────────────────────────────────

  if (stage === "selecting") {
    const grouped = groupByLevel(subjects);
    const levelOrder = ["Grade7", "O", "A"];
    const sortedEntries = Object.entries(grouped).sort(
      ([a], [b]) => levelOrder.indexOf(a) - levelOrder.indexOf(b)
    );

    return (
      <div className="max-w-2xl mx-auto px-4 py-10 space-y-8">
        {upgradeOverlay}
        <div>
          <h1 className="text-2xl font-bold text-foreground">Practice Mode</h1>
          <p className="text-muted-foreground mt-1">Choose a subject to start adaptive practice</p>
        </div>

        {subjectsLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-20 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        )}
        {error && <p className="text-red-600 text-sm">{error}</p>}

        {sortedEntries.map(([level, subs]) => (
          <div key={level} className="space-y-3">
            <div className="flex items-center gap-2">
              <span className={cn("text-xs font-semibold px-2.5 py-0.5 rounded-full border", LEVEL_COLORS[level] ?? "bg-muted text-muted-foreground border-border")}>
                {level === "Grade7" ? "Grade 7" : level === "O" ? "O Level" : "A Level"}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {subs.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSubject(s)}
                  disabled={s.paper_count === 0}
                  className={cn(
                    "text-left border rounded-xl px-5 py-4 transition-all hover:shadow-sm group",
                    s.paper_count > 0
                      ? "border-border bg-card hover:border-primary/40 hover:bg-primary/5"
                      : "border-border/50 bg-muted/30 opacity-50 cursor-not-allowed"
                  )}
                >
                  <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
                    {s.name}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {s.paper_count > 0
                      ? `${s.paper_count} paper${s.paper_count !== 1 ? "s" : ""} · Adaptive practice`
                      : "No papers yet"}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // ── Practice area ────────────────────────────────────────────────────────────

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {upgradeOverlay}

      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <button
          onClick={() => { setStage("paper-select"); setQuestion(null); setResult(null); setSessionId(null); }}
          className="text-muted-foreground hover:text-foreground transition text-sm"
        >
          ←
        </button>
        <div>
          <h1 className="font-bold text-foreground text-lg">{selectedSubject?.name}</h1>
          <p className="text-xs text-muted-foreground">
            {selectedPaperNumber ? `Paper ${selectedPaperNumber}` : "All Papers"} · {selectedSubject?.level} Level
          </p>
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-3 mb-5 p-3 rounded-2xl bg-card border border-border flex-wrap">
        <div className="flex items-center gap-1.5">
          <span className="text-lg">⚡</span>
          <div>
            <p className="text-base font-bold text-primary leading-none">{xp}</p>
            <p className="text-xs text-muted-foreground">XP</p>
          </div>
        </div>
        <div className="w-px h-8 bg-border" />
        {streak > 0 && (
          <>
            <div className="flex items-center gap-1.5">
              <span className="text-lg">🔥</span>
              <div>
                <p className="text-base font-bold text-orange-500 leading-none">{streak}</p>
                <p className="text-xs text-muted-foreground">Streak</p>
              </div>
            </div>
            <div className="w-px h-8 bg-border" />
          </>
        )}
        <div>
          <p className="text-base font-bold text-foreground leading-none">{doneCount}</p>
          <p className="text-xs text-muted-foreground">Done</p>
        </div>
        {accuracy !== null && (
          <>
            <div className="w-px h-8 bg-border" />
            <div>
              <p className={cn("text-base font-bold leading-none",
                accuracy >= 70 ? "text-green-600" : accuracy >= 50 ? "text-amber-600" : "text-red-600"
              )}>
                {accuracy}%
              </p>
              <p className="text-xs text-muted-foreground">Accuracy</p>
            </div>
          </>
        )}
      </div>

      <div className="flex gap-6">
        {/* Main column */}
        <div className="flex-1 min-w-0 space-y-4">
          {/* Topic filters */}
          {topics.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none -mx-4 px-4">
              {[null, ...topics].map((t) => (
                <button
                  key={t ?? "all"}
                  onClick={() => { setActiveTopic(t); fetchNextQuestion(t); }}
                  className={cn(
                    "shrink-0 px-3 py-1.5 rounded-full text-xs font-medium border transition-all",
                    activeTopic === t
                      ? "bg-foreground text-background border-foreground"
                      : "border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"
                  )}
                >
                  {t ?? "All topics"}
                </button>
              ))}
            </div>
          )}

          {/* Question card */}
          {questionLoading && (
            <div className="border border-border rounded-2xl p-6 space-y-4 animate-pulse">
              <div className="h-4 bg-muted rounded w-1/4" />
              <div className="h-4 bg-muted rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-1/2" />
            </div>
          )}

          {error && !questionLoading && (
            <div className="border border-red-200 bg-red-50 rounded-2xl p-6 text-red-700 text-sm text-center">
              {error}
              <button onClick={() => fetchNextQuestion(activeTopic)} className="block mx-auto mt-3 text-xs underline">
                Try again
              </button>
            </div>
          )}

          {question && !questionLoading && (
            <div className="border border-border rounded-2xl bg-card overflow-hidden">
              {/* Question header */}
              <div className="px-5 pt-5 pb-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    {question.topic_tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {question.topic_tags.map((t) => (
                          <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="text-foreground text-base leading-relaxed font-medium">
                      <MathText text={question.text} />
                    </div>
                  </div>
                  <span className="shrink-0 text-xs font-semibold text-muted-foreground bg-muted px-2.5 py-1 rounded-full whitespace-nowrap">
                    {question.marks} mark{question.marks !== 1 ? "s" : ""}
                  </span>
                </div>

                {/* Question image */}
                {question.image_url && (
                  <div className="rounded-xl border border-border bg-white overflow-hidden">
                    <div className="px-3 py-1.5 border-b border-border bg-muted/30 text-xs text-muted-foreground font-medium">
                      Figure / Diagram
                    </div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={question.image_url}
                      alt="Question diagram"
                      className="w-full max-h-72 object-contain p-4"
                      style={{ background: "white" }}
                    />
                  </div>
                )}
              </div>

              {/* Answer area */}
              {!result && (
                <div className="px-5 pb-5 space-y-4 border-t border-border pt-4">
                  {question.question_type === "mcq" ? (
                    <div className="grid grid-cols-1 gap-2.5">
                      {MCQ_OPTIONS.map((opt, idx) => {
                        const colors = OPTION_COLORS[opt];
                        const sel = answer === opt;
                        return (
                          <button
                            key={opt}
                            onClick={() => setAnswer(sel ? "" : opt)}
                            className={cn(
                              "flex items-center gap-4 border-2 rounded-xl p-3.5 text-left transition-all duration-150",
                              sel ? colors.selected : cn("bg-white", colors.base)
                            )}
                          >
                            <span className={cn(
                              "shrink-0 w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold text-white",
                              sel ? colors.badge : "bg-muted text-muted-foreground"
                            )}>
                              {opt}
                            </span>
                            <span className="text-sm font-medium text-foreground flex-1">
                              Option {opt}
                              <span className="block text-xs text-muted-foreground font-normal">Press {idx + 1}</span>
                            </span>
                            {sel && <span className="text-primary font-bold ml-auto">✓</span>}
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex rounded-xl bg-muted p-1 w-fit gap-1">
                        {(["text", "photo"] as const).map((tab) => (
                          <button
                            key={tab}
                            onClick={() => setAnswerTab(tab)}
                            className={cn(
                              "px-4 py-1.5 rounded-lg text-sm font-medium transition-all",
                              answerTab === tab
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                            )}
                          >
                            {tab === "text" ? "✏ Write" : "📷 Photo"}
                          </button>
                        ))}
                      </div>

                      {answerTab === "text" ? (
                        <textarea
                          rows={6}
                          placeholder="Write your answer here…"
                          value={answer}
                          onChange={(e) => setAnswer(e.target.value)}
                          className="w-full border border-border rounded-xl px-4 py-3 text-sm text-foreground bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring leading-relaxed"
                        />
                      ) : (
                        <div>
                          {answerImageUrl ? (
                            <div className="relative rounded-xl border border-border overflow-hidden">
                              {/* eslint-disable-next-line @next/next/no-img-element */}
                              <img src={answerImageUrl} alt="Your answer" className="w-full max-h-52 object-contain bg-white p-2" />
                              <button
                                onClick={() => setAnswerImageUrl(null)}
                                className="absolute top-2 right-2 bg-black/60 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs"
                              >✕</button>
                              <p className="text-center text-xs text-muted-foreground py-1.5 bg-muted/40">Photo answer ✓</p>
                            </div>
                          ) : (
                            <div
                              onClick={() => imageRef.current?.click()}
                              className="border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center gap-2 cursor-pointer hover:border-primary/50 hover:bg-muted/30 transition"
                            >
                              <span className="text-3xl">{imageUploading ? "⏳" : "📷"}</span>
                              <p className="text-sm font-medium">
                                {imageUploading ? "Uploading…" : "Tap to upload photo answer"}
                              </p>
                              <p className="text-xs text-muted-foreground">JPG, PNG, or HEIC</p>
                            </div>
                          )}
                          <input
                            ref={imageRef}
                            type="file"
                            accept="image/*"
                            capture="environment"
                            className="hidden"
                            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleImageFile(f); }}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  <button
                    onClick={handleSubmit}
                    disabled={submitting || (!answer.trim() && !answerImageUrl)}
                    className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-bold text-sm hover:opacity-90 transition disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {submitting ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                        Marking…
                      </span>
                    ) : "Submit Answer"}
                  </button>
                </div>
              )}

              {/* Feedback */}
              {result && (
                <div className="px-5 pb-5 border-t border-border pt-4">
                  <FeedbackCard
                    result={result}
                    question={question}
                    onNext={() => fetchNextQuestion(activeTopic)}
                    onFlag={handleFlag}
                    flagged={flagged}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Weak topics sidebar */}
        {weakTopics.length > 0 && (
          <aside className="hidden lg:block w-52 shrink-0 space-y-4">
            <p className="text-sm font-semibold text-foreground">Focus Areas</p>
            <div className="space-y-3">
              {weakTopics.slice(0, 6).map((wt) => (
                <button
                  key={wt.topic}
                  onClick={() => { setActiveTopic(wt.topic); fetchNextQuestion(wt.topic); }}
                  className="w-full text-left space-y-1.5 hover:opacity-80 transition group"
                >
                  <div className="flex justify-between text-xs">
                    <span className="truncate text-foreground group-hover:text-primary transition">{wt.topic}</span>
                    <span className="text-red-500 ml-1 shrink-0">{Math.round(wt.fail_ratio * 100)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-red-400 rounded-full" style={{ width: `${wt.fail_ratio * 100}%` }} />
                  </div>
                </button>
              ))}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
