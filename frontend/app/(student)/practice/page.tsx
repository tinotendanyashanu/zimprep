"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  getSubjects, getPracticeSession, getNextQuestion, getSubjectTopics,
  getWeakTopics, submitAttempt, flagAttempt, getPapersForSubject,
  type Subject, type Question, type PracticeAttemptResult, type WeakTopic, type MCQOption,
} from "@/lib/api";
import { UpgradePrompt } from "@/components/UpgradePrompt";
import { useQuota } from "@/hooks/useQuota";
import { MathText } from "@/components/math-text";
import { cn } from "@/lib/utils";
import { useStudent } from "@/lib/student-context";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, Flame, Target as TargetIcon, Zap, ArrowRight, CheckCircle2, AlertTriangle, Image as ImageIcon, Check } from "lucide-react";

// ── Constants ──────────────────────────────────────────────────────────────────

const premiumCard = "bg-white rounded-3xl ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgba(0,0,0,0.04)]";

const MCQ_OPTIONS = ["A", "B", "C", "D"] as const;
const OPTION_COLORS = {
  A: { base: "border-blue-100 hover:border-blue-300 hover:bg-blue-50/50", selected: "border-blue-500 bg-blue-50 ring-4 ring-blue-500/10", badge: "bg-blue-500 text-white" },
  B: { base: "border-emerald-100 hover:border-emerald-300 hover:bg-emerald-50/50", selected: "border-emerald-500 bg-emerald-50 ring-4 ring-emerald-500/10", badge: "bg-emerald-500 text-white" },
  C: { base: "border-amber-100 hover:border-amber-300 hover:bg-amber-50/50", selected: "border-amber-500 bg-amber-50 ring-4 ring-amber-500/10", badge: "bg-amber-500 text-white" },
  D: { base: "border-rose-100 hover:border-rose-300 hover:bg-rose-50/50", selected: "border-rose-500 bg-rose-50 ring-4 ring-rose-500/10", badge: "bg-rose-500 text-white" },
};
const LEVEL_COLORS: Record<string, string> = {
  Grade7: "bg-sky-100 text-sky-700 border-sky-200",
  O: "bg-emerald-100 text-emerald-700 border-emerald-200",
  A: "bg-purple-100 text-purple-700 border-purple-200",
};
const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
};

const containerVars = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } }
} as const;

const itemVars = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
} as const;

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
  onFlag: (reason: "question_issue" | "marking_issue") => void;
  flagged: boolean;
}) {
  const [picking, setPicking] = useState(false);
  const score = result.ai_score ?? 0;
  const pct = question.marks > 0 ? score / question.marks : 0;
  const isGood = pct >= 0.7;
  const isPerfect = pct >= 1;
  const msg = isPerfect ? "Perfect! 🎉" : pct >= 0.7 ? "Well done!" : pct >= 0.4 ? "Getting there 📖" : "Keep going 💪";
  const xp = score * 10;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn(
      "rounded-[2rem] p-6 sm:p-8 space-y-6 shadow-xl border-2 relative overflow-hidden",
      isGood ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
    )}>
      {isGood && <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-300/20 blur-3xl rounded-full" />}

      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center shrink-0", isGood ? "bg-emerald-100 text-emerald-600" : "bg-amber-100 text-amber-600")}>
             {isGood ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
          </div>
          <div>
            <p className={cn("font-black text-xl leading-tight", isGood ? "text-emerald-800" : "text-amber-800")}>{msg}</p>
            {xp > 0 && <p className="text-xs font-bold text-emerald-600 mt-1 uppercase tracking-widest text-left">+{xp} XP Earned</p>}
          </div>
        </div>
        <div className="text-right">
          <span className={cn(
            "font-black text-2xl tracking-tighter block leading-none mb-1",
            isGood ? "text-emerald-700" : "text-amber-700"
          )}>
            {score}/{question.marks}
          </span>
          <span className={cn("text-[10px] font-bold uppercase tracking-widest opacity-60", isGood ? "text-emerald-800" : "text-amber-800")}>Marks</span>
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
            isGood ? "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20" : "bg-amber-500 hover:bg-amber-600 shadow-amber-500/20"
          )}
        >
          Continue <ArrowRight className="h-5 w-5" />
        </button>
        {flagged ? (
          <span className="w-full sm:w-auto px-6 py-4 bg-white/50 text-gray-400 font-bold rounded-2xl text-center border border-gray-200">
            Flagged
          </span>
        ) : picking ? (
          <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto">
            <button onClick={() => { onFlag("question_issue"); setPicking(false); }} className="py-2 px-4 bg-white border border-gray-200 rounded-xl text-xs font-bold text-gray-600 hover:bg-gray-50 transition">Question Content</button>
            <button onClick={() => { onFlag("marking_issue"); setPicking(false); }} className="py-2 px-4 bg-white border border-gray-200 rounded-xl text-xs font-bold text-gray-600 hover:bg-gray-50 transition">Marking Accuracy</button>
            <button onClick={() => setPicking(false)} className="py-2 px-4 col-span-2 text-gray-500 font-bold text-xs hover:bg-black/5 rounded-xl transition">Cancel</button>
          </div>
        ) : (
          <button
            onClick={() => setPicking(true)}
            className="w-full sm:w-auto px-6 py-4 bg-white text-gray-500 hover:text-gray-900 border border-transparent hover:border-gray-200 shadow-sm hover:shadow font-bold rounded-2xl transition-all"
          >
            Report Issue
          </button>
        )}
      </div>
    </motion.div>
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

  async function handleFlag(reason: "question_issue" | "marking_issue") {
    if (!result) return;
    try { await flagAttempt(result.id, reason); setFlagged(true); } catch {}
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

  // ── Subsets ────────────────────────────────────────────────────────

  if (stage === "selecting") {
    const grouped = groupByLevel(subjects);
    const levelOrder = ["Grade7", "O", "A"];
    const sortedEntries = Object.entries(grouped).sort(
      ([a], [b]) => levelOrder.indexOf(a) - levelOrder.indexOf(b)
    );

    return (
      <motion.div variants={containerVars} initial="hidden" animate="show" className="min-h-screen bg-[#F8F9FA] px-6 py-10 lg:py-16 selection:bg-primary/20">
        <div className="max-w-3xl mx-auto space-y-10">
          {upgradeOverlay}
          <motion.div variants={itemVars} className="text-center sm:text-left flex flex-col sm:flex-row items-center gap-6">
            <div className="w-16 h-16 bg-blue-100 rounded-[1.5rem] flex items-center justify-center text-blue-600 shrink-0">
               <TargetIcon className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-gray-900 tracking-tight">Practice Arena</h1>
              <p className="text-gray-500 font-medium text-lg mt-1">Select a subject to begin adaptive training.</p>
            </div>
          </motion.div>

          {subjectsLoading && (
            <div className="grid gap-4 sm:grid-cols-2">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="h-32 rounded-3xl bg-gray-200/50 animate-pulse" />
              ))}
            </div>
          )}
          {error && <div className="bg-red-50 text-red-700 p-4 rounded-2xl font-medium">{error}</div>}

          <div className="space-y-10">
            {sortedEntries.map(([level, subs]) => (
              <motion.div variants={itemVars} key={level} className="space-y-4">
                <div className="flex items-center gap-3 px-1">
                  <span className={cn("text-xs font-black uppercase tracking-widest px-3 py-1.5 rounded-full border", LEVEL_COLORS[level] ?? "bg-gray-100 text-gray-500 border-gray-200")}>
                    {LEVEL_LABELS[level] ?? `${level} Level`}
                  </span>
                  <div className="flex-1 h-px bg-gray-200" />
                </div>            
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {subs.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => selectSubject(s)}
                      disabled={s.paper_count === 0}
                      className={cn(
                        "text-left p-6 w-full flex flex-col justify-between transition-all duration-300 group outline-none",
                        s.paper_count > 0
                          ? cn(premiumCard, "hover:scale-[1.02] active:scale-[0.98] hover:ring-primary/20", selectedSubject?.id === s.id ? "ring-2 ring-primary bg-primary/5" : "")
                          : "bg-gray-50 rounded-3xl ring-1 ring-gray-200 opacity-60 cursor-not-allowed"
                      )}
                    >
                      <div className="mb-4">
                        <p className="font-extrabold text-xl text-gray-900 group-hover:text-primary transition-colors leading-tight">
                          {s.name}
                        </p>
                        <p className="text-sm font-semibold text-gray-500 mt-1">
                          {s.paper_count > 0
                            ? `${s.paper_count} standard paper${s.paper_count !== 1 ? "s" : ""}`
                            : "No papers yet"}
                        </p>
                      </div>
                      <div className="flex items-center justify-between mt-auto pt-2">
                        <span className={cn("text-[10px] font-black uppercase tracking-widest", s.paper_count > 0 ? "text-primary bg-primary/10 px-3 py-1.5 rounded-xl" : "text-gray-400 bg-gray-200 px-3 py-1.5 rounded-xl")}>
                          {s.paper_count > 0 ? "Start Run" : "Unavailable"}
                        </span>
                        <ArrowRight className={cn("w-5 h-5 transition-transform", s.paper_count > 0 ? "text-primary group-hover:translate-x-1" : "text-gray-400")} />
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    );
  }

  // ── Paper selection ──────────────────────────────────────────────────────────

  if (stage === "paper-select" && selectedSubject) {
    const PAPER_LABELS: Record<number, string> = {
      1: "Multiple Choice Questions",
      2: "Structured / Theory",
      3: "Practical / Extended",
      4: "Advanced Theory",
    };

    return (
      <motion.div variants={containerVars} initial="hidden" animate="show" className="min-h-screen bg-[#F8F9FA] px-6 py-10 lg:py-16 selection:bg-primary/20">
        <div className="max-w-3xl mx-auto space-y-10">
          {upgradeOverlay}
          <motion.div variants={itemVars} className="flex items-center gap-4">
            <button
              onClick={() => { setStage("selecting"); setSelectedSubject(null); }}
              className="w-12 h-12 rounded-full bg-white ring-1 ring-black/5 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all active:scale-95"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <div>
              <h1 className="text-3xl font-black text-gray-900 tracking-tight">{selectedSubject.name}</h1>
              <p className="text-gray-500 font-medium text-lg mt-1">Select a specific paper format</p>
            </div>
          </motion.div>

          {error && <p className="bg-red-50 text-red-700 p-4 rounded-2xl font-medium">{error}</p>}

          <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {availablePaperNumbers.map((num) => (
              <button
                key={num}
                onClick={() => startPractice(num)}
                className={cn(premiumCard, "p-6 flex flex-col text-left hover:scale-[1.02] active:scale-[0.98] transition-all group outline-none")}
              >
                <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  <span className="font-extrabold text-lg">P{num}</span>
                </div>
                <p className="font-extrabold text-xl text-gray-900 group-hover:text-primary transition-colors">
                  Paper {num}
                </p>
                <p className="text-sm font-semibold text-gray-500 mt-1 mb-4 flex-1">
                  {PAPER_LABELS[num] ?? `Paper ${num} questions`}
                </p>
                <span className="text-[10px] font-black uppercase tracking-widest text-primary bg-primary/10 px-3 py-1.5 rounded-xl w-fit">
                   Start Paper {num}
                </span>
              </button>
            ))}
            
            <button
              onClick={() => startPractice(null)}
              className={cn(premiumCard, "p-6 flex flex-col text-left hover:scale-[1.02] active:scale-[0.98] transition-all group outline-none sm:col-span-2 border-2 border-transparent hover:border-primary/20 bg-gradient-to-br from-white to-primary/5")}
            >
               <div className="w-12 h-12 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors">
                  <TargetIcon className="w-6 h-6" />
                </div>
              <p className="font-extrabold text-xl text-gray-900 group-hover:text-primary transition-colors">
                All Papers (Endless Mode)
              </p>
              <p className="text-sm font-semibold text-gray-500 mt-1">
                Adaptive practice traversing all available paper formats.
              </p>
              <div className="mt-4 flex justify-end">
                  <ArrowRight className="w-6 h-6 text-primary group-hover:translate-x-1 transition-transform" />
              </div>
            </button>
          </motion.div>
        </div>
      </motion.div>
    );
  }

  // ── Practice area ────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[#F8F9FA] px-4 py-8 pb-32 sm:pb-12 text-gray-900">
      <div className="max-w-4xl mx-auto space-y-6">
        {upgradeOverlay}

        {/* Dynamic Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => { setStage("paper-select"); setQuestion(null); setResult(null); setSessionId(null); }}
              className="w-10 h-10 rounded-full bg-white ring-1 ring-black/5 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all active:scale-95 shrink-0"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="font-black text-xl tracking-tight text-gray-900">{selectedSubject?.name}</h1>
              <p className="text-[11px] font-black uppercase tracking-widest text-gray-500">
                {selectedPaperNumber ? `Paper ${selectedPaperNumber}` : "Endless Mode"} · {LEVEL_LABELS[selectedSubject?.level ?? ""] ?? `${selectedSubject?.level} Level`}
              </p>
            </div>
          </div>

          {/* Gamified Stats Pill */}
          <div className="bg-white rounded-[2rem] p-3 shadow-md ring-1 ring-black/5 flex items-center gap-4 self-start sm:self-auto shrink-0 w-full sm:w-auto overflow-x-auto scrollbar-none">
            <div className="flex items-center gap-2 pl-2">
              <Zap className="h-5 w-5 text-yellow-400 fill-yellow-400 drop-shadow-sm" />
              <div className="flex flex-col">
                <span className="font-black leading-none text-base text-gray-900">{xp}</span>
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-400">XP</span>
              </div>
            </div>
            <div className="w-px h-8 bg-gray-100" />
            <div className="flex items-center gap-2">
              <Flame className={cn("h-5 w-5 drop-shadow-sm", streak > 0 ? "text-orange-500 fill-orange-500" : "text-gray-300")} />
              <div className="flex flex-col">
                <span className={cn("font-black leading-none text-base", streak > 0 ? "text-orange-600" : "text-gray-400")}>{streak}</span>
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-400">Streak</span>
              </div>
            </div>
            <div className="w-px h-8 bg-gray-100" />
            <div className="flex items-center gap-2">
              <TargetIcon className="h-5 w-5 text-blue-500 drop-shadow-sm" />
              <div className="flex flex-col">
                <span className="font-black leading-none text-base text-gray-900">{doneCount}</span>
                <span className="text-[9px] font-black uppercase tracking-widest text-gray-400">Done</span>
              </div>
            </div>
            {accuracy !== null && (
              <>
                <div className="w-px h-8 bg-gray-100" />
                <div className="flex flex-col pr-2">
                  <span className={cn("font-black leading-none text-base", accuracy >= 70 ? "text-emerald-500" : accuracy >= 50 ? "text-amber-500" : "text-red-500")}>
                    {accuracy}%
                  </span>
                  <span className="text-[9px] font-black uppercase tracking-widest text-gray-400">Acc</span>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex gap-6 items-start">
          {/* Main Column */}
          <div className="flex-1 min-w-0 space-y-6">
            
            {/* Horizontal Filter Pill List */}
            {topics.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none -mx-4 px-4 sm:mx-0 sm:px-0">
                {[null, ...topics].map((t) => (
                  <button
                    key={t ?? "all"}
                    onClick={() => { setActiveTopic(t); fetchNextQuestion(t); }}
                    className={cn(
                      "shrink-0 px-4 py-2 rounded-2xl text-[11px] font-black uppercase tracking-wide transition-all",
                      activeTopic === t
                        ? "bg-gray-900 text-white shadow-md shadow-gray-900/20"
                        : "bg-white text-gray-500 ring-1 ring-gray-200 hover:ring-gray-300 hover:bg-gray-50"
                    )}
                  >
                    {t ?? "All Sylabus Topics"}
                  </button>
                ))}
              </div>
            )}

            {questionLoading && (
              <div className={cn(premiumCard, "p-8 space-y-6 animate-pulse")}>
                <div className="flex justify-between items-center">
                   <div className="h-6 w-24 bg-gray-200 rounded-full" />
                   <div className="h-6 w-16 bg-gray-200 rounded-full" />
                </div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded-full w-full" />
                  <div className="h-4 bg-gray-200 rounded-full w-5/6" />
                  <div className="h-4 bg-gray-200 rounded-full w-4/6" />
                </div>
                <div className="space-y-3 pt-6">
                  <div className="h-16 bg-gray-100 rounded-2xl w-full" />
                  <div className="h-16 bg-gray-100 rounded-2xl w-full" />
                </div>
              </div>
            )}

            {error && !questionLoading && (
              <div className={cn(premiumCard, "p-10 text-center bg-red-50/50 flex flex-col items-center justify-center border border-red-100")}>
                <AlertTriangle className="h-10 w-10 text-red-500 mb-4" />
                <p className="text-red-700 font-bold mb-4">{error}</p>
                <button onClick={() => fetchNextQuestion(activeTopic)} className="px-6 py-3 bg-white text-gray-900 ring-1 ring-gray-200 focus:ring-0 shadow-sm rounded-xl font-bold hover:bg-gray-50 transition active:scale-95">
                  Load Next Mission
                </button>
              </div>
            )}

            {question && !questionLoading && (
              <AnimatePresence mode="wait">
              <motion.div key={question.id} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }} className={cn(premiumCard, "overflow-hidden flex flex-col")}>
                
                {/* Question Top Section */}
                <div className="p-6 sm:p-8 space-y-6 border-b border-gray-100 bg-white">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-3 flex-1 flex flex-col items-start">
                      {question.topic_tags?.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {question.topic_tags.map((t) => (
                            <span key={t} className="text-[10px] px-3 py-1 rounded-xl font-black uppercase tracking-widest bg-blue-50 text-blue-600">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                      
                      <div className="text-gray-900 text-lg sm:text-xl font-semibold leading-relaxed tracking-tight">
                        <MathText text={getQuestionStem(question)} />
                      </div>
                    </div>
                    <div className="shrink-0 flex flex-col items-end">
                       <span className="text-[10px] font-black uppercase tracking-widest text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-100 shadow-sm">
                         {question.marks} Mark{question.marks !== 1 ? "s" : ""}
                       </span>
                    </div>
                  </div>

                  {question.image_url && (
                    <div className="rounded-[1.5rem] border-2 border-gray-100 bg-gray-50/50 overflow-hidden mt-6 relative group">
                      <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-widest text-gray-500 shadow-sm">
                        Figure
                      </div>
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={question.image_url}
                        alt="Question diagram"
                        className="w-full h-auto max-h-[400px] object-contain p-6 mix-blend-multiply"
                      />
                    </div>
                  )}
                </div>

                {/* Answer Area */}
                {!result && (
                  <div className="p-6 sm:p-8 bg-gray-50/30 flex flex-col flex-1">
                    {question.question_type === "mcq" ? (
                      <div className="grid grid-cols-1 gap-3 sm:gap-4 flex-1">
                        {getMcqOptions(question).map((opt, idx) => {
                          const colors = OPTION_COLORS[opt.letter as keyof typeof OPTION_COLORS] ?? OPTION_COLORS.A;
                          const sel = answer === opt.letter;
                          return (
                            <button
                              key={opt.letter}
                              onClick={() => setAnswer(sel ? "" : opt.letter)}
                              className={cn(
                                "flex items-center gap-4 rounded-2xl p-4 sm:p-5 text-left transition-all duration-200 outline-none border-2 shadow-sm min-h-[72px] sm:min-h-[80px]",
                                sel ? cn(colors.selected, "scale-[1.01] sm:scale-[1.02] translate-x-1 sm:translate-x-0") : cn("bg-white border-transparent shadow", colors.base)
                              )}
                            >
                              <span className={cn(
                                "shrink-0 w-12 h-12 rounded-[14px] flex items-center justify-center text-lg font-black transition-colors duration-300 shadow-sm",
                                sel ? colors.badge : "bg-gray-100 text-gray-400 group-hover:bg-gray-200"
                              )}>
                                {opt.letter}
                              </span>
                              <span className={cn("text-base sm:text-lg font-semibold flex-1 leading-snug tracking-tight", sel ? "text-gray-900" : "text-gray-700")}>
                                <MathText text={opt.text} />
                              </span>
                              <div className={cn("w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all", sel ? "border-primary bg-primary text-white scale-110" : "border-gray-200 text-transparent")}>
                                <Check className="w-3.5 h-3.5" strokeWidth={3} />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="space-y-4 flex-1 flex flex-col">
                         <div className="flex bg-gray-200/50 p-1 rounded-2xl w-fit self-center sm:self-start mb-2 shadow-inner">
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
                            rows={8}
                            placeholder="Type your detailed answer logically here..."
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            className="w-full flex-1 border-2 border-gray-100 rounded-3xl p-6 text-base text-gray-900 bg-white placeholder:text-gray-300 resize-none focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary shadow-inner transition-all leading-relaxed"
                          />
                        ) : (
                          <div className="flex-1 flex flex-col justify-center">
                            {answerImageUrl ? (
                              <div className="relative rounded-3xl border-2 border-gray-100 bg-white overflow-hidden shadow-sm">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img src={answerImageUrl} alt="Your answer" className="w-full max-h-64 object-contain p-4" />
                                <button
                                  onClick={() => setAnswerImageUrl(null)}
                                  className="absolute top-4 right-4 bg-gray-900/80 backdrop-blur text-white rounded-full w-10 h-10 flex items-center justify-center text-sm font-black shadow-lg hover:bg-red-500 transition-colors"
                                >✕</button>
                              </div>
                            ) : (
                              <div
                                onClick={() => imageRef.current?.click()}
                                className="border-[3px] border-dashed border-gray-200 bg-white/50 rounded-3xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-primary/40 hover:bg-primary/5 transition-all outline-none"
                              >
                                <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-[1.5rem] flex items-center justify-center pointer-events-none">
                                  {imageUploading ? <Zap className="w-8 h-8 animate-pulse" /> : <ImageIcon className="w-8 h-8" />}
                                </div>
                                <div className="text-center">
                                  <p className="text-lg font-extrabold text-gray-900">
                                    {imageUploading ? "Processing visual..." : "Snap & upload working"}
                                  </p>
                                  <p className="text-sm font-semibold text-gray-400 mt-1">Accepts standard image formats.</p>
                                </div>
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

                    {/* Submit Area - Fixed Bottom Mobile, Inline Desktop */}
                     <div className="fixed inset-x-0 bottom-0 z-50 p-4 bg-white/80 backdrop-blur-xl border-t border-black/5 shadow-[0_-10px_40px_rgba(0,0,0,0.05)] sm:static sm:p-0 sm:bg-transparent sm:border-0 sm:shadow-none sm:pt-6 mt-auto">
                        <button
                          onClick={handleSubmit}
                          disabled={submitting || (!answer.trim() && !answerImageUrl)}
                          className={cn(
                            "w-full py-4 sm:py-5 rounded-[1.5rem] font-black text-lg tracking-wide transition-all shadow-xl flex items-center justify-center gap-2",
                            (answer.trim() || answerImageUrl) 
                              ? "bg-primary text-white hover:bg-blue-600 shadow-primary/30 hover:shadow-primary/40 active:translate-y-1 hover:-translate-y-0.5" 
                              : "bg-gray-100 text-gray-400 shadow-none cursor-not-allowed"
                          )}
                        >
                          {submitting ? (
                            <><Zap className="w-5 h-5 animate-pulse" /> Evaluating...</>
                          ) : "Check Answer"}
                        </button>
                     </div>
                  </div>
                )}

                {/* Feedback Region */}
                {result && (
                  <div className="p-6 sm:p-8 bg-gray-50/50">
                    <FeedbackCard
                      result={result}
                      question={question}
                      onNext={() => fetchNextQuestion(activeTopic)}
                      onFlag={handleFlag}
                      flagged={flagged}
                    />
                  </div>
                )}

              </motion.div>
              </AnimatePresence>
            )}
          </div>

          {/* Weak topics sidebar plugin (Desktop only) */}
          {weakTopics.length > 0 && (
            <aside className="hidden lg:flex w-[260px] flex-col shrink-0 space-y-4">
              <div className="bg-white rounded-[2rem] p-6 shadow-sm ring-1 ring-black/5 flex flex-col gap-5 sticky top-8">
                 <div className="flex items-center gap-3">
                   <div className="bg-red-50 p-2 rounded-xl text-red-500">
                      <TargetIcon className="w-5 h-5" />
                   </div>
                   <p className="font-extrabold text-gray-900 tracking-tight">Focus Engine</p>
                 </div>
                 
                 <div className="space-y-4 pt-1">
                   {weakTopics.slice(0, 5).map((wt) => (
                     <button
                       key={wt.topic}
                       onClick={() => { setActiveTopic(wt.topic); fetchNextQuestion(wt.topic); }}
                       className="w-full text-left group outline-none"
                     >
                       <div className="flex items-end justify-between text-xs mb-2">
                         <span className="font-bold text-gray-700 group-hover:text-primary transition-colors line-clamp-1 flex-1 pr-2">{wt.topic}</span>
                         <span className="font-black text-red-500 shrink-0">{Math.round(wt.fail_ratio * 100)}% Miss</span>
                       </div>
                       <div className="h-2 rounded-full bg-gray-100 overflow-hidden shadow-inner">
                         <div className="h-full bg-red-400 rounded-full transition-all group-hover:bg-red-500" style={{ width: `${wt.fail_ratio * 100}%` }} />
                       </div>
                     </button>
                   ))}
                  </div>
                  <div className="mt-2 pt-4 border-t border-gray-100">
                    <p className="text-[10px] font-bold text-gray-400 leading-tight">These topics are auto-prioritized in Endless Mode to build competence.</p>
                  </div>
              </div>
            </aside>
          )}

        </div>
      </div>
    </div>
  );
}
