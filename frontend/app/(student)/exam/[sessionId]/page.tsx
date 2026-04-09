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
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Zap, Target as TargetIcon, ArrowRight, ArrowLeft, CheckCircle2, Image as ImageIcon, Send, X, ClipboardCheck, AlertTriangle, Maximize2, Check } from "lucide-react";

// ── Constants ──────────────────────────────────────────────────────────────────

const MCQ_OPTIONS = ["A", "B", "C", "D"] as const;
const OPTION_COLORS = {
  A: { base: "border-blue-100 hover:border-blue-300 hover:bg-blue-50/50", selected: "border-blue-500 bg-blue-50 ring-4 ring-blue-500/10", badge: "bg-blue-500 text-white" },
  B: { base: "border-emerald-100 hover:border-emerald-300 hover:bg-emerald-50/50", selected: "border-emerald-500 bg-emerald-50 ring-4 ring-emerald-500/10", badge: "bg-emerald-500 text-white" },
  C: { base: "border-amber-100 hover:border-amber-300 hover:bg-amber-50/50", selected: "border-amber-500 bg-amber-50 ring-4 ring-amber-500/10", badge: "bg-amber-500 text-white" },
  D: { base: "border-rose-100 hover:border-rose-300 hover:bg-rose-50/50", selected: "border-rose-500 bg-rose-50 ring-4 ring-rose-500/10", badge: "bg-rose-500 text-white" },
};

const premiumCard = "bg-white rounded-[2rem] ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgba(0,0,0,0.04)]";

// ── Helpers ────────────────────────────────────────────────────────────────────

function getMcqOptions(q: Question): MCQOption[] {
  if (q.mcq_options && q.mcq_options.length > 0) return q.mcq_options;
  const lines = q.text.split(/\n/);
  const opts: MCQOption[] = [];
  for (const line of lines) {
    const m = line.match(/^\s*([A-D])[.\s\)]+(.+)/);
    if (m) opts.push({ letter: m[1] as "A" | "B" | "C" | "D", text: m[2].trim() });
  }
  return opts.length >= 2 ? opts : MCQ_OPTIONS.map((l) => ({ letter: l, text: `Option ${l}` }));
}

function getQuestionStem(q: Question): string {
  if (q.question_type !== "mcq") return q.text;
  if (q.mcq_options && q.mcq_options.length > 0) return q.text;
  return q.text.split(/\n/).filter((l) => !/^\s*[A-D][.\s\)]/.test(l)).join("\n").trim();
}

function formatTime(s: number) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`
    : `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
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
      <div className="rounded-[1.5rem] border-2 border-gray-100 bg-gray-50/50 overflow-hidden mt-6 relative group inline-block w-full">
        <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-widest text-gray-500 shadow-sm z-10 pointer-events-none">
          Figure
        </div>
        <button 
          onClick={() => setLightbox(true)}
          className="absolute top-3 right-3 bg-black/50 hover:bg-black/80 backdrop-blur text-white p-2 rounded-xl transition-all z-10 opacity-0 group-hover:opacity-100"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={url}
          alt="Question diagram"
          onClick={() => setLightbox(true)}
          className="w-full h-auto max-h-[400px] object-contain cursor-zoom-in p-6 mix-blend-multiply"
        />
      </div>
      {lightbox && (
        <div
          className="fixed inset-0 bg-black/90 z-100 flex items-center justify-center p-4 cursor-zoom-out backdrop-blur-sm"
          onClick={() => setLightbox(false)}
        >
           <div className="absolute top-6 right-6">
              <button onClick={() => setLightbox(false)} className="bg-white/10 text-white p-3 rounded-full hover:bg-white/20 transition backdrop-blur-md">
                 <X className="w-6 h-6" />
              </button>
           </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={url} alt="Diagram" className="max-w-[95vw] max-h-[90vh] object-contain rounded-2xl shadow-2xl" />
        </div>
      )}
    </>
  );
}

function PracticeFeedback({ result, question, onNext, onRetry }: {
  result: Attempt; question: Question; onNext: () => void; onRetry: () => void;
}) {
  const score = result.ai_score ?? 0;
  const pct = question.marks > 0 ? score / question.marks : 0;
  const isGood = pct >= 0.7;
  const isPerfect = pct >= 1;
  const isMcq = question.question_type === "mcq";
  const msg = isMcq
    ? (score === question.marks ? "Correct! 🎉" : "Incorrect")
    : (isPerfect ? "Perfect! 🎉" : pct >= 0.7 ? "Well done!" : pct >= 0.4 ? "Getting there 📖" : "Keep practising 💪");

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn(
      "rounded-4xl p-6 sm:p-8 space-y-6 shadow-xl border-2 relative overflow-hidden",
      isGood ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"
    )}>
      {isGood && <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-300/20 blur-3xl rounded-full" />}

      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 shadow-inner", isGood ? "bg-emerald-100 text-emerald-600" : "bg-red-100 text-red-600")}>
             {isGood ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
          </div>
          <p className={cn("font-black text-xl leading-tight", isGood ? "text-emerald-800" : "text-red-800")}>{msg}</p>
        </div>
        <div className="text-right">
          <span className={cn(
            "font-black text-2xl tracking-tighter block leading-none mb-1",
            isGood ? "text-emerald-700" : "text-red-700"
          )}>
            {score}/{question.marks}
          </span>
          <span className={cn("text-[10px] font-bold uppercase tracking-widest opacity-60", isGood ? "text-emerald-800" : "text-red-800")}>Marks</span>
        </div>
      </div>

      {result.ai_feedback && (
        <div className="space-y-4 text-sm relative z-10 bg-white/60 p-5 rounded-3xl border border-white/40 shadow-sm">
          {result.ai_feedback.correct_points.length > 0 && (
            <div>
              <p className="font-extrabold text-emerald-700 mb-2 flex items-center gap-1.5"><Check className="h-4 w-4" /> Correct Points</p>
              <ul className="space-y-1.5 pl-5 border-l-[3px] border-emerald-300 text-gray-600">
                {result.ai_feedback.correct_points.map((p, i) => (
                  <li key={i} className="font-medium"><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.missing_points.length > 0 && (
            <div className={result.ai_feedback.correct_points.length > 0 ? "pt-2" : ""}>
              <p className="font-extrabold text-red-600 mb-2 flex items-center gap-1.5"><TargetIcon className="h-4 w-4" /> Missing Points</p>
              <ul className="space-y-1.5 pl-5 border-l-[3px] border-red-300 text-gray-600">
                {result.ai_feedback.missing_points.map((p, i) => (
                  <li key={i} className="font-medium"><MathText text={p} /></li>
                ))}
              </ul>
            </div>
          )}
          {result.ai_feedback.examiner_note && (
             <div className="pt-2 border-t border-black/5 mt-2">
                 <p className="font-extrabold text-gray-800 mb-1 flex items-center gap-1.5 text-xs uppercase tracking-widest">Examiner Insight</p>
                 <MathText text={result.ai_feedback.examiner_note} className="text-gray-600 font-medium italic" />
             </div>
          )}
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 pt-2 relative z-10">
        <button
          onClick={onNext}
           className={cn("w-full py-4 text-white rounded-2xl font-extrabold text-base transition-all sm:flex-1 shadow-lg hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2", 
            isGood ? "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20" : "bg-gray-900 hover:bg-black shadow-zinc-500/20"
          )}
        >
          Next Question <ArrowRight className="h-5 w-5" />
        </button>
        <button
          onClick={onRetry}
          className="w-full sm:w-auto px-6 py-4 bg-white text-gray-500 hover:text-gray-900 border border-transparent hover:border-gray-200 shadow-sm hover:shadow font-bold rounded-2xl transition-all"
        >
          Retry Problem
        </button>
      </div>
    </motion.div>
  );
}

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
    <div className="space-y-4 flex-1 flex flex-col justify-center">
      {imageUrl ? (
        <div className="relative rounded-3xl border-2 border-gray-100 bg-white overflow-hidden shadow-sm">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={imageUrl} alt="Your answer" className="w-full max-h-64 object-contain p-4" />
          <button
            onClick={() => onUpload("")}
            className="absolute top-4 right-4 bg-gray-900/80 backdrop-blur text-white rounded-full w-10 h-10 flex items-center justify-center text-sm font-black shadow-lg hover:bg-red-500 transition-colors"
          >
            ✕
          </button>
          <div className="absolute top-4 left-4 bg-emerald-500 text-white rounded-xl px-3 py-1 text-[10px] font-black uppercase tracking-widest shadow-sm">
            Photo Attached
          </div>
        </div>
      ) : (
        <div
          onClick={() => ref.current?.click()}
          className="border-[3px] border-dashed border-gray-200 bg-white/50 rounded-3xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-primary/40 hover:bg-primary/5 transition-all outline-none h-full min-h-[240px]"
        >
          <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-[1.5rem] flex items-center justify-center pointer-events-none shadow-inner">
             {uploading ? <Zap className="w-8 h-8 animate-pulse" /> : <ImageIcon className="w-8 h-8" />}
          </div>
          <div className="text-center">
            <p className="text-lg font-extrabold text-gray-900">
               {uploading ? "Processing upload..." : "Tap to scan your working"}
            </p>
            <p className="text-sm font-semibold text-gray-400 mt-1">Accepts JPG, PNG, or HEIC</p>
          </div>
        </div>
      )}
      <input ref={ref} type="file" accept="image/*" capture="environment" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      {error && <p className="text-xs font-bold text-red-600 text-center">{error}</p>}
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
        if (saved) {
          try {
            const parsed = JSON.parse(saved);
            if (parsed && typeof parsed === "object" && ("answers" in parsed || "answerImages" in parsed)) {
              setAnswers(parsed.answers ?? {});
              setAnswerImages(parsed.answerImages ?? {});
            } else {
              setAnswers(parsed ?? {});
            }
          } catch {}
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId, router]);

  useEffect(() => {
    if (loading || session?.mode !== "exam") return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          handleSubmitExam(answersRef.current, answerImagesRef.current);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, session?.mode]);

  useEffect(() => {
    if (Object.keys(answers).length > 0 || Object.keys(answerImages).length > 0) {
      localStorage.setItem(`exam_${sessionId}`, JSON.stringify({ answers, answerImages }));
    }
  }, [answers, answerImages, sessionId]);

  useEffect(() => {
    if (loading) return;
    const interval = setInterval(() => {
      if (Object.keys(answersRef.current).length > 0 || Object.keys(answerImagesRef.current).length > 0) {
        autosaveSession(sessionId, answersRef.current, answerImagesRef.current).catch(() => {});
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [loading, sessionId]);

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
    async (
      currentAnswers: Record<string, string>,
      currentAnswerImages: Record<string, string>,
    ) => {
      if (submitting) return;
      setSubmitting(true);
      try {
        await submitSession(sessionId, currentAnswers, currentAnswerImages);
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
    <div className="flex bg-[#F8F9FA] items-center justify-center min-h-screen flex-col gap-6">
      <div className="w-16 h-16 rounded-3xl bg-primary/20 flex items-center justify-center">
         <div className="w-8 h-8 rounded-full border-4 border-primary/30 border-t-primary animate-spin" />
      </div>
      <p className="text-sm font-black uppercase tracking-widest text-gray-400">Loading Environment</p>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-[#F8F9FA] px-6 py-12 flex justify-center items-center">
      <div className={cn(premiumCard, "w-full max-w-md p-10 text-center flex flex-col items-center")}>
         <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
         <p className="font-extrabold text-xl text-gray-900 mb-2">Access Denied</p>
         <p className="text-red-600 mb-8 font-medium">{error}</p>
         <button onClick={() => router.push("/dashboard")} className="w-full py-4 bg-gray-900 text-white rounded-2xl font-bold active:scale-95 transition-all shadow-lg hover:bg-black">
           Return to Dashboard
         </button>
      </div>
    </div>
  );

  if (questions.length === 0) return (
    <div className="min-h-screen bg-[#F8F9FA] px-6 py-12 flex justify-center items-center">
      <div className={cn(premiumCard, "w-full max-w-md p-10 text-center")}>
        <p className="text-gray-500 font-bold">No data payload found for this specific run.</p>
      </div>
    </div>
  );

  const currentQ = questions[currentIdx];
  const isExamMode = session?.mode === "exam";
  const hasMcq = questions.some((q) => q.question_type === "mcq");
  const isBatchMode = isExamMode || hasMcq;
  const answeredCount = questions.filter((q) => answers[q.id] || answerImages[q.id]).length;
  const progressPct = (answeredCount / questions.length) * 100;
  const unansweredCount = questions.length - answeredCount;

  const timerUrgent = timeLeft < 300;
  const timerWarning = timeLeft < 600;

  return (
    <div className="flex flex-col min-h-screen bg-[#F8F9FA] selection:bg-primary/20 text-gray-900">
      
      {/* Top Bar Area */}
      <div className="bg-white border-b border-gray-100 z-40 sticky top-0 shadow-sm">
        
        {/* Dynamic Progress Strip */}
        <div className="relative h-1.5 bg-gray-100 w-full overflow-hidden">
          <div
            className={cn("absolute top-0 left-0 h-full transition-all duration-700 rounded-r-full shadow-[0_0_10px_rgba(0,0,0,0.2)]", isExamMode ? "bg-red-500" : "bg-primary")}
            style={{ width: `${progressPct}%` }}
          />
        </div>

        <div className="px-4 pr-3 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0 flex-1">
             <div className={cn("hidden sm:flex w-10 h-10 rounded-xl items-center justify-center shrink-0 shadow-inner", isExamMode ? "bg-red-50 text-red-600" : "bg-indigo-50 text-indigo-600")}>
                {isExamMode ? <Clock className="w-5 h-5" /> : <ClipboardCheck className="w-5 h-5" />}
             </div>
             <div className="min-w-0">
               <p className="text-sm font-extrabold text-gray-900 truncate">
                 {session?.paper?.subject?.name}
               </p>
               <p className="text-[11px] font-black uppercase tracking-widest text-gray-400 truncate mt-0.5">
                 Paper {session?.paper?.paper_number} • Progress: {answeredCount}/{questions.length}
               </p>
             </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {isExamMode && (
              <div className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl transition-colors ring-1",
                timerUrgent ? "text-red-600 bg-red-50 ring-red-200 animate-pulse" :
                timerWarning ? "text-amber-600 bg-amber-50 ring-amber-200" : "text-gray-700 bg-gray-50 ring-gray-200"
              )}>
                <Clock className="w-4 h-4" />
                <span className="font-mono text-sm font-black tracking-tight self-center leading-none mt-0.5">
                  {formatTime(timeLeft)}
                </span>
              </div>
            )}
            {isBatchMode && (
              <button
                onClick={() => setShowConfirm(true)}
                disabled={submitting}
                className={cn(
                  "px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-sm transition-all active:scale-95",
                  submitting ? "bg-gray-100 text-gray-400 cursor-not-allowed" :
                  isExamMode ? "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20" : "bg-gray-900 hover:bg-black text-white"
                )}
              >
                {submitting ? "Processing..." : isExamMode ? "End Exam" : "Finish Run"}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden h-[calc(100vh-68px)]">
        
        {/* Desktop Question Map Sidebar */}
        <aside className="hidden md:flex w-[100px] border-r border-gray-100 bg-white flex-col py-6 overflow-y-auto scrollbar-none items-center shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-10 shrink-0">
          <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-6 text-center">Questions</p>
          <div className="flex flex-col gap-3 px-2 w-full">
            {questions.map((q, i) => {
              const done = !!(answers[q.id] || answerImages[q.id]);
              return (
                <button
                  key={q.id}
                  onClick={() => { setCurrentIdx(i); setAnswerTab("text"); }}
                  className={cn(
                    "w-full aspect-square rounded-[1rem] text-sm font-black transition-all flex items-center justify-center outline-none shrink-0",
                    i === currentIdx
                      ? "bg-gray-900 text-white shadow-lg shadow-gray-900/20 scale-105"
                      : done
                        ? "bg-green-50 text-green-600 ring-2 ring-green-100 hover:bg-green-100"
                        : "bg-gray-50 text-gray-400 ring-1 ring-gray-200 hover:bg-gray-100 hover:text-gray-600"
                  )}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 w-full flex flex-col items-center bg-[#F8F9FA] overflow-y-auto px-4 sm:px-8 py-6 sm:py-10 pb-32 sm:pb-12">
          <div className="w-full max-w-3xl flex-1 flex flex-col space-y-6 lg:space-y-8 min-h-full">
            
            {/* Mobile Horizontal Nav */}
            <div className="flex md:hidden gap-3 overflow-x-auto pb-2 scrollbar-none -mx-4 px-4 sm:mx-0 sm:px-0">
              {questions.map((q, i) => {
                const done = !!(answers[q.id] || answerImages[q.id]);
                return (
                  <button
                    key={q.id}
                    onClick={() => { setCurrentIdx(i); setAnswerTab("text"); }}
                    className={cn(
                      "shrink-0 w-12 h-12 rounded-[1rem] text-sm font-black transition-all outline-none",
                      i === currentIdx 
                        ? "bg-gray-900 text-white shadow-md shadow-gray-900/20" 
                        : done 
                          ? "bg-green-50 text-green-600 ring-2 ring-green-100" 
                          : "bg-white text-gray-400 ring-1 ring-gray-200"
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
                initial={{ opacity: 0, scale: 0.98, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.98, y: -10 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className={cn(premiumCard, "w-full overflow-hidden flex flex-col")}
              >
                {/* Question Info Header */}
                <div className="px-6 py-6 sm:px-8 sm:py-8 border-b border-gray-100 bg-white flex flex-col">
                  
                  <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-widest text-gray-500">
                        Prompt {currentQ.question_number}{currentQ.sub_question ? `(${currentQ.sub_question})` : ""}
                      </span>
                      {currentQ.section && (
                        <span className="text-[10px] font-black uppercase tracking-widest bg-gray-100 px-2.5 py-1 rounded-xl text-gray-500">
                          Sec {currentQ.section}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-xl border border-indigo-100">
                      {currentQ.marks} Mark{currentQ.marks !== 1 ? "s" : ""}
                    </span>
                  </div>

                  <div className="text-gray-900 text-lg sm:text-xl font-semibold leading-relaxed tracking-tight">
                    <MathText text={getQuestionStem(currentQ)} />
                  </div>

                  {currentQ.image_url && <QuestionImage url={currentQ.image_url} />}
                </div>

                {/* Interactive Answer Area */}
                {!practiceResults[currentQ.id] && (
                  <div className="p-6 sm:p-8 bg-gray-50/50 flex flex-col flex-1">
                    
                    {currentQ.question_type === "mcq" ? (
                      <div className="grid grid-cols-1 gap-3 sm:gap-4 h-full">
                        {getMcqOptions(currentQ).map((opt, idx) => {
                          const colors = OPTION_COLORS[opt.letter as keyof typeof OPTION_COLORS] ?? OPTION_COLORS.A;
                          const selected = answers[currentQ.id] === opt.letter;
                          return (
                            <button
                              key={opt.letter}
                              onClick={() => handleAnswerChange(currentQ.id, opt.letter)}
                              className={cn(
                                "flex items-center gap-4 border-2 rounded-2xl p-4 sm:p-5 text-left transition-all duration-200 outline-none shadow-sm min-h-[72px] sm:min-h-[80px]",
                                selected ? cn(colors.selected, "scale-[1.01] sm:scale-[1.02] translate-x-1 sm:translate-x-0") : cn(colors.base, "bg-white border-transparent shadow")
                              )}
                            >
                              <span className={cn(
                                "shrink-0 w-12 h-12 rounded-[14px] flex items-center justify-center text-lg font-black transition-colors duration-300 shadow-sm",
                                selected ? colors.badge : "bg-gray-100 text-gray-400 opacity-60"
                              )}>
                                {opt.letter}
                              </span>
                              <span className={cn("text-base sm:text-lg font-semibold flex-1 leading-snug tracking-tight", selected ? "text-gray-900" : "text-gray-700")}>
                                <MathText text={opt.text} />
                              </span>
                              <div className={cn("w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all", selected ? "border-primary bg-primary text-white scale-110" : "border-gray-200 text-transparent")}>
                                <Check className="w-3.5 h-3.5" strokeWidth={3} />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="space-y-4 flex flex-col h-full">
                        <div className="flex bg-gray-200/50 p-1 rounded-2xl w-fit mb-2 shadow-inner">
                          {(["text", "photo"] as const).map((tab) => (
                            <button
                              key={tab}
                              onClick={() => setAnswerTab(tab)}
                              className={cn(
                                "px-6 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center gap-2",
                                answerTab === tab
                                  ? "bg-white text-gray-900 shadow-md"
                                  : "text-gray-500 hover:text-gray-700"
                              )}
                            >
                              {tab === "text" ? "Keyboard" : <><ImageIcon className="w-4 h-4"/> Photo</>}
                            </button>
                          ))}
                        </div>

                        {answerTab === "text" ? (
                          <textarea
                            value={answers[currentQ.id] ?? ""}
                            onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
                            placeholder="Draft your detailed analysis here..."
                            rows={8}
                            className="w-full flex-1 border-2 border-gray-100 rounded-3xl p-6 text-base text-gray-900 bg-white placeholder:text-gray-300 resize-none focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary shadow-inner transition-all leading-relaxed"
                          />
                        ) : (
                          <ImageUploadArea
                            sessionId={sessionId}
                            imageUrl={answerImages[currentQ.id] ?? null}
                            onUpload={(url) => {
                              setAnswerImages((prev) => ({ ...prev, [currentQ.id]: url }));
                              setPracticeResults((prev) => {
                                const next = { ...prev };
                                delete next[currentQ.id];
                                return next;
                              });
                            }}
                          />
                        )}
                      </div>
                    )}

                    {/* Instant Submits for Practice Theory Mode */}
                    {!isBatchMode && !practiceResults[currentQ.id] && currentQ.question_type !== "mcq" && (
                      <div className="mt-6">
                        <button
                          onClick={handleSubmitPractice}
                          disabled={practiceSubmitting || (!answers[currentQ.id]?.trim() && !answerImages[currentQ.id])}
                          className={cn(
                             "w-full py-4 rounded-[1.5rem] font-black text-lg transition-all shadow-lg flex items-center justify-center gap-2",
                             (answers[currentQ.id]?.trim() || answerImages[currentQ.id]) 
                              ? "bg-primary text-white hover:bg-blue-600 active:scale-95 shadow-primary/30"
                              : "bg-gray-100 text-gray-400 shadow-none cursor-not-allowed"
                          )}
                        >
                          {practiceSubmitting ? <Zap className="w-5 h-5 animate-pulse" /> : "Assess Correctness"}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Instant Feedback Area */}
                {practiceResults[currentQ.id] && (
                  <div className="p-6 sm:p-8 bg-gray-50/80">
                    <PracticeFeedback
                      result={practiceResults[currentQ.id]}
                      question={currentQ}
                      onNext={goToNext}
                      onRetry={() => handleRetry(currentQ.id)}
                    />
                  </div>
                )}

              </motion.div>
            </AnimatePresence>
            
            {/* Nav Controls */}
            {!practiceResults[currentQ.id] && (
              <div className="fixed inset-x-0 bottom-0 z-45 bg-white/80 backdrop-blur-xl border-t border-black/5 p-4 sm:static sm:bg-transparent sm:backdrop-blur-none sm:border-0 sm:p-0 flex gap-4 mt-auto">
                <button
                  disabled={currentIdx === 0}
                  onClick={() => { setCurrentIdx((i) => i - 1); setAnswerTab("text"); }}
                  className="flex-1 py-4 sm:py-5 rounded-[1.5rem] font-black text-base text-gray-600 bg-white ring-2 ring-gray-200 hover:ring-gray-300 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ArrowLeft className="w-5 h-5" /> Prev
                </button>
                <button
                  disabled={currentIdx === questions.length - 1}
                  onClick={() => { setCurrentIdx((i) => i + 1); setAnswerTab("text"); }}
                  className="flex-1 py-4 sm:py-5 rounded-[1.5rem] font-black text-base text-gray-900 bg-white ring-2 ring-gray-900 shadow-lg hover:bg-gray-50 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Skip <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            )}

          </div>
        </main>
      </div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setShowConfirm(false)} />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className={cn(premiumCard, "w-full max-w-sm relative z-10 overflow-hidden flex flex-col p-8 text-center")}
            >
               <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-[1.5rem] flex items-center justify-center mx-auto mb-5 shadow-inner">
                 <Send className="w-8 h-8" />
               </div>
               <h2 className="text-2xl font-black text-gray-900 mb-2">Finalize Protocol</h2>
               <p className="text-gray-500 font-semibold mb-8">
                 {unansweredCount > 0
                   ? `You are omitting ${unansweredCount} prompt${unansweredCount !== 1 ? "s" : ""}. Proceed regardless?`
                   : "All systems green. Transmit payload to evaluator?"}
               </p>
               <div className="flex flex-col gap-3">
                 <button
                   onClick={() => {
                     setShowConfirm(false);
                     handleSubmitExam(answersRef.current, answerImagesRef.current);
                   }}
                   disabled={submitting}
                   className="w-full py-4 bg-gray-900 text-white rounded-2xl font-black text-base active:scale-95 transition-all shadow-lg hover:bg-black flex items-center justify-center gap-2"
                 >
                   {submitting ? <><Zap className="w-5 h-5 animate-pulse" /> Processing...</> : "Confirm Upload"}
                 </button>
                 <button
                   onClick={() => setShowConfirm(false)}
                   className="w-full py-4 bg-gray-100 text-gray-600 rounded-2xl font-bold text-base hover:bg-gray-200 transition-colors"
                 >
                   Abort
                 </button>
               </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
