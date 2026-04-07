"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getSession, getQuestionsForPaper, autosaveSession, submitSession, submitAttempt,
  type Session, type Question, type Attempt, type MCQOption,
} from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";
import { MathText } from "@/components/math-text";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

// ── Constants ──────────────────────────────────────────────────────────────────

const MCQ_OPTIONS = ["A", "B", "C", "D"] as const;
const OPTION_COLORS = {
  A: { base: "border-blue-200   bg-blue-50   hover:border-blue-400",   selected: "border-blue-500   bg-blue-100",   badge: "bg-blue-500"   },
  B: { base: "border-green-200  bg-green-50  hover:border-green-400",  selected: "border-green-500  bg-green-100",  badge: "bg-green-500"  },
  C: { base: "border-amber-200  bg-amber-50  hover:border-amber-400",  selected: "border-amber-500  bg-amber-100",  badge: "bg-amber-500"  },
  D: { base: "border-rose-200   bg-rose-50   hover:border-rose-400",   selected: "border-rose-500   bg-rose-100",   badge: "bg-rose-500"   },
};

// ── Helpers ────────────────────────────────────────────────────────────────────

/**
 * Extract MCQ option texts. Uses structured mcq_options if present,
 * otherwise falls back to parsing A./B./C./D. lines from question text.
 */
function getMcqOptions(q: Question): MCQOption[] {
  if (q.mcq_options && q.mcq_options.length > 0) return q.mcq_options;
  // Fallback: parse "A  text", "B. text", "A) text" patterns from question text
  const lines = q.text.split(/\n/);
  const opts: MCQOption[] = [];
  for (const line of lines) {
    const m = line.match(/^\s*([A-D])[.\s\)]+(.+)/);
    if (m) opts.push({ letter: m[1], text: m[2].trim() });
  }
  return opts.length >= 2 ? opts : MCQ_OPTIONS.map((l) => ({ letter: l, text: `Option ${l}` }));
}

/**
 * Strip A/B/C/D option lines from a question's text so the stem renders cleanly.
 */
function getQuestionStem(q: Question): string {
  if (q.question_type !== "mcq") return q.text;
  if (q.mcq_options && q.mcq_options.length > 0) {
    // Options are stored separately — text should already be stem-only
    return q.text;
  }
  // Remove option lines from the text
  return q.text.split(/\n/).filter((l) => !/^\s*[A-D][.\s\)]/.test(l)).join("\n").trim();
}

function formatTime(s: number) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`
    : `${m}:${String(sec).padStart(2, "0")}`;
}

async function uploadAnswerImage(file: File, sessionId: string): Promise<string> {
  const supabase = createClient();
  const ext = file.name.split(".").pop() ?? "jpg";
  const path = `${sessionId}/${Date.now()}.${ext}`;
  const { error } = await supabase.storage.from("answer-images").upload(path, file, { upsert: true });
  if (error) throw new Error(error.message);
  const { data } = supabase.storage.from("answer-images").getPublicUrl(path);
  return data.publicUrl;
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function QuestionImage({ url }: { url: string }) {
  const [lightbox, setLightbox] = useState(false);
  return (
    <>
      <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
        <div className="px-3 py-1.5 border-b border-border bg-muted/40 flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-medium">Figure / Diagram</span>
          <button onClick={() => setLightbox(true)} className="ml-auto text-xs text-primary hover:underline">
            Expand ↗
          </button>
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={url}
          alt="Question diagram"
          onClick={() => setLightbox(true)}
          className="w-full max-h-72 object-contain cursor-zoom-in p-4"
          style={{ background: "white" }}
        />
      </div>
      {lightbox && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setLightbox(false)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={url} alt="Diagram" className="max-w-full max-h-full object-contain rounded-lg" />
        </div>
      )}
    </>
  );
}

function ScoreBadge({ score, max }: { score: number; max: number }) {
  const pct = max > 0 ? score / max : 0;
  const color = pct >= 0.7 ? "text-green-600 bg-green-50 border-green-200"
    : pct >= 0.4 ? "text-amber-600 bg-amber-50 border-amber-200"
    : "text-red-600 bg-red-50 border-red-200";
  const emoji = pct >= 0.7 ? "✓" : pct >= 0.4 ? "~" : "✗";
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-sm font-semibold", color)}>
      {emoji} {score}/{max} marks
    </span>
  );
}

function PracticeFeedback({ result, question, onNext, onRetry }: {
  result: Attempt; question: Question; onNext: () => void; onRetry: () => void;
}) {
  const score = result.ai_score ?? 0;
  const pct = question.marks > 0 ? score / question.marks : 0;
  const isGood = pct >= 0.7;
  const isMcq = question.question_type === "mcq";
  const isCorrect = isMcq && score === question.marks;
  const msg = isMcq
    ? (isCorrect ? "Correct!" : "Incorrect")
    : (pct >= 1 ? "Perfect!" : pct >= 0.7 ? "Well done! ✓" : pct >= 0.4 ? "Getting there 📖" : "Keep practising 💪");

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
      "rounded-2xl border p-6 space-y-4 shadow-sm",
      isGood ? "border-green-200 bg-green-50/60" : "border-red-100 bg-red-50/40"
    )}>
      <div className="flex items-center justify-between">
        <p className={cn("font-semibold text-base", isGood ? "text-green-700" : "text-red-700")}>{msg}</p>
        <ScoreBadge score={score} max={question.marks} />
      </div>

      {result.ai_feedback && (
        <div className="space-y-3 text-sm">
          {result.ai_feedback.correct_points.length > 0 && (
            <div>
              <p className="font-medium text-green-700 mb-1">✓ Correct</p>
              <ul className="space-y-0.5 text-muted-foreground pl-3 border-l-2 border-green-200">
                {result.ai_feedback.correct_points.map((p, i) => (
                  <li key={i}><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.missing_points.length > 0 && (
            <div>
              <p className="font-medium text-red-700 mb-1">✗ Missing</p>
              <ul className="space-y-0.5 text-muted-foreground pl-3 border-l-2 border-red-200">
                {result.ai_feedback.missing_points.map((p, i) => (
                  <li key={i}><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.examiner_note && (
            <div className="bg-white/80 rounded-lg px-4 py-3 border border-border text-muted-foreground">
              <span className="font-medium text-foreground">Examiner: </span>
              <MathText text={result.ai_feedback.examiner_note} />
            </div>
          )}
        </div>
      )}

      {result.ai_references && result.ai_references.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {result.ai_references.map((r, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-white border border-border text-muted-foreground">
              {r}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <Button onClick={onNext} size="lg" className="w-full sm:flex-1">
          Next Question →
        </Button>
        <Button onClick={onRetry} size="lg" variant="outline" className="w-full sm:w-auto">
          Try Again
        </Button>
      </div>
    </motion.div>
  );
}

// ── Image upload area ──────────────────────────────────────────────────────────

function ImageUploadArea({ sessionId, onUpload, imageUrl }: {
  sessionId: string;
  onUpload: (url: string) => void;
  imageUrl: string | null;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    if (!file.type.startsWith("image/")) { setError("Please select an image file"); return; }
    setUploading(true);
    setError(null);
    try {
      const url = await uploadAnswerImage(file, sessionId);
      onUpload(url);
    } catch {
      setError("Upload failed. Try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-3">
      {imageUrl ? (
        <div className="relative rounded-xl border border-border overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={imageUrl} alt="Your answer" className="w-full max-h-64 object-contain bg-white p-2" />
          <button
            onClick={() => onUpload("")}
            className="absolute top-2 right-2 bg-black/60 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-black/80"
          >
            ✕
          </button>
          <p className="text-xs text-center text-muted-foreground py-1.5 bg-muted/40">
            Photo answer uploaded ✓
          </p>
        </div>
      ) : (
        <div
          onClick={() => ref.current?.click()}
          className="border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center gap-2 cursor-pointer hover:border-primary/50 hover:bg-muted/30 transition-colors"
        >
          <span className="text-3xl">📷</span>
          <p className="text-sm font-medium text-foreground">
            {uploading ? "Uploading…" : "Tap to upload a photo of your answer"}
          </p>
          <p className="text-xs text-muted-foreground">JPG, PNG, or HEIC</p>
        </div>
      )}
      <input ref={ref} type="file" accept="image/*" capture="environment" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function ExamSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [session, setSession] = useState<Session | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [answerImages, setAnswerImages] = useState<Record<string, string>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(120 * 60);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [answerTab, setAnswerTab] = useState<"text" | "photo">("text");

  const [practiceResults, setPracticeResults] = useState<Record<string, Attempt>>({});
  const [practiceSubmitting, setPracticeSubmitting] = useState(false);

  const answersRef = useRef(answers);
  const answerImagesRef = useRef(answerImages);
  answersRef.current = answers;
  answerImagesRef.current = answerImages;

  useEffect(() => {
    async function load() {
      try {
        const s = await getSession(sessionId);
        if (s.status !== "active") { router.replace(`/exam/${sessionId}/results`); return; }
        setSession(s);
        setTimeLeft((s.paper?.duration_minutes ?? 120) * 60);
        const qs = await getQuestionsForPaper(s.paper_id);
        setQuestions(qs);
        const saved = localStorage.getItem(`exam_${sessionId}`);
        if (saved) { try { setAnswers(JSON.parse(saved)); } catch {} }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId, router]);

  // Countdown
  useEffect(() => {
    if (loading || session?.mode !== "exam") return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) { clearInterval(interval); handleSubmitExam(answersRef.current); return 0; }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, session?.mode]);

  // Autosave
  useEffect(() => {
    if (Object.keys(answers).length > 0) localStorage.setItem(`exam_${sessionId}`, JSON.stringify(answers));
  }, [answers, sessionId]);

  useEffect(() => {
    if (loading) return;
    const interval = setInterval(() => {
      if (Object.keys(answersRef.current).length > 0)
        autosaveSession(sessionId, answersRef.current).catch(() => {});
    }, 30_000);
    return () => clearInterval(interval);
  }, [loading, sessionId]);

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
      if (e.key === "ArrowRight") setCurrentIdx((i) => Math.min(i + 1, questions.length - 1));
      if (e.key === "ArrowLeft") setCurrentIdx((i) => Math.max(i - 1, 0));
      if (["1","2","3","4"].includes(e.key) && questions[currentIdx]?.question_type === "mcq") {
        const opt = MCQ_OPTIONS[parseInt(e.key) - 1];
        if (opt) handleAnswerChange(questions[currentIdx].id, opt);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [questions, currentIdx]);

  const handleSubmitExam = useCallback(
    async (currentAnswers: Record<string, string>) => {
      if (submitting) return;
      setSubmitting(true);
      try {
        await submitSession(sessionId, currentAnswers);
        localStorage.removeItem(`exam_${sessionId}`);
        router.push(`/exam/${sessionId}/results`);
      } catch (e) {
        setError((e as Error).message);
        setSubmitting(false);
      }
    },
    [sessionId, router, submitting],
  );

  async function handleSubmitPractice() {
    const q = questions[currentIdx];
    if (!q) return;
    const ans = answers[q.id] ?? "";
    const img = answerImages[q.id] ?? undefined;
    if (!ans.trim() && !img) return;
    setPracticeSubmitting(true);
    try {
      const result = await submitAttempt(sessionId, q.id, ans, img);
      setPracticeResults((prev) => ({ ...prev, [q.id]: result }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPracticeSubmitting(false);
    }
  }

  function handleAnswerChange(questionId: string, value: string) {
    setPracticeResults((prev) => { const next = { ...prev }; delete next[questionId]; return next; });
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  function goToNext() {
    setCurrentIdx((i) => Math.min(i + 1, questions.length - 1));
    setAnswerTab("text");
  }

  function handleRetry(questionId: string) {
    setPracticeResults((prev) => { const next = { ...prev }; delete next[questionId]; return next; });
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-[80vh] flex-col gap-4">
      <div className="w-10 h-10 rounded-full border-4 border-border border-t-primary animate-spin" />
      <p className="text-sm text-muted-foreground">Loading paper…</p>
    </div>
  );

  if (error) return (
    <div className="max-w-md mx-auto px-6 py-16 text-center">
      <p className="text-red-600 mb-4">{error}</p>
      <button onClick={() => router.push("/dashboard")} className="btn-secondary text-sm">
        Back to dashboard
      </button>
    </div>
  );

  if (questions.length === 0) return (
    <div className="max-w-md mx-auto px-6 py-16 text-center text-muted-foreground">
      No questions found for this paper.
    </div>
  );

  const currentQ = questions[currentIdx];
  const isExamMode = session?.mode === "exam";
  // Papers with any MCQ questions use batch submit in both modes
  const hasMcq = questions.some((q) => q.question_type === "mcq");
  const isBatchMode = isExamMode || hasMcq;
  const answeredCount = questions.filter((q) => answers[q.id] || answerImages[q.id]).length;
  const progressPct = (answeredCount / questions.length) * 100;
  const unansweredCount = questions.length - answeredCount;

  const timerUrgent = timeLeft < 300;
  const timerWarning = timeLeft < 600;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Progress strip */}
      <div className="h-1 bg-muted w-full">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Top bar */}
      <div className="border-b border-border bg-background sticky top-0 z-40">
        <div className="px-4 py-2.5 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {session?.paper?.subject?.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {session?.paper?.year}
              {session?.paper?.exam_session && (
                <span className="capitalize"> ({session.paper.exam_session})</span>
              )}
              {" · "}Paper {session?.paper?.paper_number} · {answeredCount}/{questions.length} answered
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {isExamMode && (
              <span className={cn(
                "font-mono text-sm font-bold px-3 py-1 rounded-lg",
                timerUrgent ? "text-red-600 bg-red-50 animate-pulse" :
                timerWarning ? "text-amber-600 bg-amber-50" : "text-foreground bg-muted"
              )}>
                {formatTime(timeLeft)}
              </span>
            )}
            {isBatchMode && (
              <button
                onClick={() => setShowConfirm(true)}
                disabled={submitting}
                className="px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
              >
                {submitting ? "Submitting…" : isExamMode ? "Submit" : "Finish & Submit"}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-1">
        {/* Question number sidebar */}
        <aside className="hidden md:flex w-20 border-r border-border flex-col py-4 px-2 gap-1 overflow-y-auto">
          {questions.map((q, i) => {
            const done = !!(answers[q.id] || answerImages[q.id]);
            return (
              <button
                key={q.id}
                onClick={() => { setCurrentIdx(i); setAnswerTab("text"); }}
                className={cn(
                  "w-12 h-10 mx-auto rounded-lg text-xs font-semibold transition-all",
                  i === currentIdx
                    ? "bg-primary text-primary-foreground shadow-sm scale-105"
                    : done
                      ? "bg-green-100 text-green-700 border border-green-200"
                      : "bg-muted text-muted-foreground hover:bg-muted/60"
                )}
              >
                {i + 1}
              </button>
            );
          })}
        </aside>

        {/* Main content */}
        <main className="flex-1 max-w-2xl mx-auto px-4 sm:px-6 py-6 pb-24 sm:pb-6 space-y-6">
          {/* Mobile question nav */}
          <div className="flex md:hidden gap-1.5 overflow-x-auto pb-2 scrollbar-none -mx-4 px-4">
            {questions.map((q, i) => {
              const done = !!(answers[q.id] || answerImages[q.id]);
              return (
                <button
                  key={q.id}
                  onClick={() => { setCurrentIdx(i); }}
                  className={cn(
                    "shrink-0 w-10 h-10 rounded-xl text-sm font-semibold transition-all",
                    i === currentIdx ? "bg-primary text-primary-foreground shadow-sm scale-105" :
                    done ? "bg-green-100 text-green-700 border border-green-200" : "bg-muted text-muted-foreground"
                  )}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentQ.id}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="space-y-6"
            >
              {/* Question header */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Question {currentQ.question_number}{currentQ.sub_question ? `(${currentQ.sub_question})` : ""}
              </span>
              {currentQ.section && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                  Section {currentQ.section}
                </span>
              )}
              <span className="ml-auto text-xs font-semibold text-muted-foreground bg-muted px-2.5 py-1 rounded-full">
                {currentQ.marks} mark{currentQ.marks !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="text-foreground text-base leading-relaxed">
              <MathText text={getQuestionStem(currentQ)} />
            </div>
          </div>

          {/* Question image */}
          {currentQ.image_url && <QuestionImage url={currentQ.image_url} />}

          {/* Answer area */}
          {!practiceResults[currentQ.id] && (
            currentQ.question_type === "mcq" ? (
              <div className="grid grid-cols-1 gap-2.5">
                {getMcqOptions(currentQ).map((opt, idx) => {
                  const colors = OPTION_COLORS[opt.letter as keyof typeof OPTION_COLORS] ?? OPTION_COLORS.A;
                  const selected = answers[currentQ.id] === opt.letter;
                  return (
                    <button
                      key={opt.letter}
                      onClick={() => handleAnswerChange(currentQ.id, opt.letter)}
                      className={cn(
                        "flex items-center gap-4 border-2 rounded-xl p-4 text-left transition-all duration-150 w-full min-h-[56px]",
                        selected ? colors.selected : cn(colors.base, "bg-white")
                      )}
                    >
                      <span className={cn(
                        "shrink-0 w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold",
                        selected ? `${colors.badge} text-white` : "bg-muted-foreground/20 text-foreground"
                      )}>
                        {opt.letter}
                      </span>
                      <span className="text-sm font-medium text-foreground flex-1 min-w-0">
                        <MathText text={opt.text} />
                        <span className="block text-xs text-muted-foreground font-normal mt-0.5">
                          Press {idx + 1}
                        </span>
                      </span>
                      {selected && (
                        <span className="ml-auto text-primary font-bold shrink-0">✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-3">
                {/* Tab switch */}
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
                    value={answers[currentQ.id] ?? ""}
                    onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
                    placeholder="Write your answer here…"
                    rows={7}
                    className="w-full border border-border rounded-xl px-4 py-3 text-sm text-foreground bg-background resize-y focus:outline-none focus:ring-2 focus:ring-ring leading-relaxed"
                  />
                ) : (
                  <ImageUploadArea
                    sessionId={sessionId}
                    imageUrl={answerImages[currentQ.id] ?? null}
                    onUpload={(url) => {
                      setAnswerImages((prev) => ({ ...prev, [currentQ.id]: url }));
                    }}
                  />
                )}
              </div>
            )
          )}

          {/* Practice submit — written questions only; MCQ uses batch submit */}
          {!isBatchMode && !practiceResults[currentQ.id] && currentQ.question_type !== "mcq" && (
            <Button
              onClick={handleSubmitPractice}
              disabled={practiceSubmitting || (!answers[currentQ.id]?.trim() && !answerImages[currentQ.id])}
              isLoading={practiceSubmitting}
              size="lg"
              className="w-full"
            >
              {practiceSubmitting ? "Marking..." : "Submit Answer"}
            </Button>
          )}

          {/* Practice feedback */}
          {practiceResults[currentQ.id] && (
            <PracticeFeedback
              result={practiceResults[currentQ.id]}
              question={currentQ}
              onNext={goToNext}
              onRetry={() => handleRetry(currentQ.id)}
            />
          )}

          {/* Navigation — sticky on mobile */}
          {!practiceResults[currentQ.id] && (
            <div className="fixed inset-x-0 bottom-[calc(5rem+env(safe-area-inset-bottom,0px))] z-50 flex gap-3 border-t border-border bg-background/95 p-4 pt-2 backdrop-blur-md safe-area-inset-bottom sm:relative sm:bottom-auto sm:inset-auto sm:z-auto sm:border-0 sm:bg-transparent sm:p-0 sm:pt-2 sm:backdrop-blur-none">
              <Button
                disabled={currentIdx === 0}
                onClick={() => { setCurrentIdx((i) => i - 1); setAnswerTab("text"); }}
                variant="outline"
                size="lg"
                className="flex-1 h-12 sm:h-auto"
              >
                ← Previous
              </Button>
              <Button
                disabled={currentIdx === questions.length - 1}
                onClick={() => { setCurrentIdx((i) => i + 1); setAnswerTab("text"); }}
                variant="outline"
                size="lg"
                className="flex-1 h-12 sm:h-auto"
              >
                Next →
              </Button>
            </div>
          )}
          </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Submit confirmation */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 px-4">
          <div className="bg-background border border-border rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-xl">
            <div className="text-center">
              <p className="text-2xl mb-2">📋</p>
              <h2 className="text-lg font-bold text-foreground">Submit exam?</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {unansweredCount > 0
                  ? `${unansweredCount} question${unansweredCount !== 1 ? "s" : ""} unanswered. This cannot be undone.`
                  : "All questions answered. Ready to submit!"}
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => { setShowConfirm(false); handleSubmitExam(answersRef.current); }}
                isLoading={submitting}
                className="flex-1"
                size="lg"
              >
                {submitting ? "Submitting…" : "Confirm"}
              </Button>
              <Button
                onClick={() => setShowConfirm(false)}
                variant="outline"
                className="flex-1"
                size="lg"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
