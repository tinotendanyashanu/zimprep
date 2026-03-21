"use client";
import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import Link from "next/link";
import {
  ArrowLeft,
  ChevronRight,
  Flag,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  BookOpen,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MIN_ANSWER_CHARS = 20;

type PracticeStatus = "loading" | "answering" | "submitting" | "reviewing" | "error";

interface PracticeQuestion {
  id: string;
  question_number: string;
  text: string;
  marks: number;
  question_type: "written" | "mcq";
  has_image: boolean;
  image_url?: string;
  topic_tags: string[];
  subject_id: string;
  mcq_answer?: { correct_option: string }[];
}

interface MarkResult {
  question_id: string;
  score: number;
  max_score: number;
  correct_points: string[];
  missing_points: string[];
  feedback_summary: string;
  study_references: string[];
}

// Simple A/B/C/D radio for MCQ in practice mode
function MCQSimple({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {["A", "B", "C", "D"].map((opt) => (
        <label
          key={opt}
          className={cn(
            "flex items-center gap-4 p-5 rounded-2xl border-4 cursor-pointer transition-all active:translate-y-1",
            value === opt
              ? "border-primary bg-primary/10 shadow-sm"
              : "border-border border-b-[6px] bg-card hover:bg-secondary/50 hover:border-border/80 text-foreground"
          )}
          style={{ borderBottomWidth: value === opt ? '4px' : undefined }}
        >
          <input
            type="radio"
            className="sr-only"
            name="mcq"
            value={opt}
            checked={value === opt}
            onChange={() => onChange(opt)}
          />
          <span
            className={cn(
              "w-10 h-10 rounded-xl border-2 flex items-center justify-center font-black text-base flex-shrink-0 shadow-sm",
              value === opt
                ? "border-primary bg-primary text-white"
                : "border-border text-muted-foreground bg-secondary"
            )}
          >
            {opt}
          </span>
          <span
            className={cn(
              "font-bold text-lg",
              value === opt ? "text-primary" : "text-foreground"
            )}
          >
            {opt}
          </span>
        </label>
      ))}
    </div>
  );
}

export default function PracticePage() {
  const searchParams = useSearchParams();
  const subjectId = searchParams.get("subject_id") || "";
  const subjectName = searchParams.get("subject") || "Practice";

  const [status, setStatus] = useState<PracticeStatus>(
    subjectId ? "loading" : "error"
  );
  const [question, setQuestion] = useState<PracticeQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<MarkResult | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [flagged, setFlagged] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [sessionScore, setSessionScore] = useState(0);
  const [sessionMax, setSessionMax] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);
  const [topicFilter, setTopicFilter] = useState("");
  const [allTopics, setAllTopics] = useState<string[]>([]);

  const loadQuestion = useCallback(async () => {
    if (!subjectId) {
      setStatus("error");
      setErrorMsg("No subject selected.");
      return;
    }
    setStatus("loading");
    setAnswer("");
    setResult(null);
    setAttemptId(null);
    setFlagged(false);
    try {
      const url = new URL(`${API_URL}/practice/next`);
      url.searchParams.set("subject_id", subjectId);
      if (topicFilter) url.searchParams.set("topic", topicFilter);
      const res = await fetch(url.toString());
      if (res.status === 404) {
        setStatus("error");
        setErrorMsg("No questions available for this subject yet.");
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const q: PracticeQuestion = await res.json();
      setQuestion(q);
      // Collect topics for filter
      if (q.topic_tags?.length) {
        setAllTopics((prev) => {
          const merged = new Set([...prev, ...q.topic_tags]);
          return Array.from(merged).sort();
        });
      }
      setStatus("answering");
    } catch (e) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Failed to load question");
    }
  }, [subjectId, topicFilter]);

  useEffect(() => {
    if (subjectId) loadQuestion();
  }, []); // eslint-disable-line

  const submitAnswer = async () => {
    if (!question) return;
    if (question.question_type === "written" && answer.length < MIN_ANSWER_CHARS)
      return;
    setStatus("submitting");
    try {
      const res = await fetch(`${API_URL}/practice/mark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: question.id,
          question_text: question.text
            .replace(/<[^>]+>/g, " ")
            .replace(/\s+/g, " ")
            .trim(),
          student_answer: answer,
          max_score: question.marks,
          question_type: question.question_type,
          topic: question.topic_tags?.[0] || "",
          subject_id: question.subject_id,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: MarkResult & { attempt_id?: string } = await res.json();
      setResult(data);
      if (data.attempt_id) setAttemptId(data.attempt_id);
      setSessionScore((s) => s + data.score);
      setSessionMax((m) => m + data.max_score);
      setQuestionCount((c) => c + 1);
      setStatus("reviewing");
    } catch (e) {
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Marking failed");
    }
  };

  const flagAnswer = async () => {
    if (!attemptId) return;
    try {
      await fetch(`${API_URL}/attempts/${attemptId}/flag`, { method: "POST" });
      setFlagged(true);
    } catch {
      /* non-fatal */
    }
  };

  const pct = result ? result.score / Math.max(result.max_score, 1) : 0;
  const scoreColor =
    pct >= 1
      ? "text-green-600"
      : pct >= 0.5
      ? "text-amber-600"
      : "text-red-600";

  if (!subjectId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-zinc-900">
            No Subject Selected
          </h1>
          <p className="text-zinc-500">
            Go to Subjects and start a practice session from there.
          </p>
          <Button asChild variant="outline">
            <Link href="/subjects">Browse Subjects</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-32">
      {/* Header */}
      <header className="h-20 border-b-4 border-border bg-card flex items-center justify-between px-6 sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-6 flex-1">
          <Link
            href="/dashboard"
            className="w-10 h-10 rounded-xl border-2 border-border flex items-center justify-center text-muted-foreground hover:bg-secondary hover:text-foreground transition-all hover:shadow-gamified hover:-translate-y-0.5 active:translate-y-0 shadow-sm block"
          >
            <ArrowLeft className="w-5 h-5 mx-auto" />
          </Link>
          {/* Progress Bar Header */}
          <div className="flex-1 max-w-xl hidden sm:block">
             <div className="h-4 w-full bg-secondary border-2 border-border/50 rounded-full overflow-hidden shadow-inner p-0.5 relative">
                <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${sessionMax > 0 ? (sessionScore / sessionMax) * 100 : 0}%` }} />
             </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {sessionMax > 0 && (
            <div className="flex items-center gap-2 bg-secondary border-2 border-border px-4 py-2 rounded-xl shadow-sm">
              <span className="text-xs font-black uppercase tracking-wider text-muted-foreground">Session</span>
              <span className="text-base font-black text-primary">{Math.round((sessionScore/sessionMax)*100)}%</span>
            </div>
          )}
          {/* Topic filter */}
          {allTopics.length > 0 && (
            <select
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
              className="text-sm font-bold border-2 border-border rounded-xl px-3 py-2 bg-card text-foreground focus:ring-2 focus:ring-primary outline-none shadow-sm cursor-pointer"
            >
              <option value="">All Topics</option>
              {allTopics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
        {/* Loading */}
        {status === "loading" && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
          </div>
        )}

        {/* Error */}
        {status === "error" && (
          <div className="text-center space-y-4 py-12">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
            <p className="text-zinc-600">{errorMsg}</p>
            <Button variant="outline" onClick={loadQuestion}>
              Try Again
            </Button>
          </div>
        )}

        {/* Answering */}
        {(status === "answering" || status === "submitting") && question && (
          <>
            <div className="bg-card border-4 border-border rounded-3xl p-8 shadow-gamified">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b-2 border-border/50">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-2xl bg-secondary flex items-center justify-center font-black text-muted-foreground border-2 border-border/50 shadow-sm">
                    Q
                  </span>
                  <div>
                      <h2 className="text-lg font-black text-foreground uppercase tracking-wide">
                        Question {question.question_number}
                      </h2>
                      {question.topic_tags?.[0] && (
                        <span className="text-xs font-bold text-muted-foreground">
                          {question.topic_tags[0]}
                        </span>
                      )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {question.question_type === "mcq" && (
                    <span className="bg-blue-100 text-blue-700 border-2 border-blue-200 px-3 py-1 rounded-xl text-xs font-black uppercase tracking-widest shadow-sm">
                      MCQ
                    </span>
                  )}
                  <span className="bg-accent/10 text-accent border-2 border-accent/20 px-3 py-1 rounded-xl text-xs font-black uppercase tracking-widest shadow-sm">
                    {question.marks} {question.marks === 1 ? "Mark" : "Marks"}
                  </span>
                </div>
              </div>
              {question.has_image && question.image_url && (
                <div className="mb-6 rounded-2xl overflow-hidden border-2 border-border shadow-sm">
                  <img
                    src={question.image_url}
                    alt="Question diagram"
                    className="max-w-full object-contain max-h-64 mx-auto block"
                  />
                </div>
              )}
              <div
                className="text-xl md:text-2xl font-semibold leading-relaxed text-foreground"
                dangerouslySetInnerHTML={{ __html: question.text }}
              />
            </div>

            <div className="my-8">
              <h3 className="text-lg font-black uppercase tracking-widest text-muted-foreground mb-6 flex items-center gap-3">
                <div className="w-2 h-6 bg-orange-400 rounded-full"></div>
                Your Answer
              </h3>
              {question.question_type === "mcq" ? (
                <MCQSimple value={answer} onChange={setAnswer} />
              ) : (
                <div className="space-y-3">
                  <textarea
                    className="w-full min-h-[220px] p-6 border-4 border-border rounded-3xl font-medium text-lg leading-relaxed focus:border-primary focus:ring-4 focus:ring-primary/20 outline-none resize-none shadow-gamified"
                    placeholder="Type your answer here..."
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    disabled={status === "submitting"}
                  />
                  <div className="flex justify-between text-sm font-bold text-muted-foreground px-4">
                    <span
                      className={cn(
                        answer.length > 0 && answer.length < MIN_ANSWER_CHARS
                          ? "text-orange-500"
                          : ""
                      )}
                    >
                      {answer.length > 0 && answer.length < MIN_ANSWER_CHARS
                        ? `Need ${MIN_ANSWER_CHARS - answer.length} more chars`
                        : `${answer.split(/\s+/).filter(Boolean).length} words`}
                    </span>
                  </div>
                </div>
              )}
            </div>

// removed normal button and substituted with fixed bottom bar below
          </>
        )}

        {/* Reviewing */}
        {status === "reviewing" && question && result && (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            <div
              className={cn(
                "bg-card border-4 rounded-3xl p-8 shadow-gamified mb-24",
                pct >= 1
                  ? "border-green-400"
                  : pct >= 0.5
                  ? "border-amber-400"
                  : "border-red-400"
              )}
            >
              <div className="flex items-center justify-between mb-6 pb-6 border-b-2 border-border/50">
                <div>
                  <p className="text-sm font-black uppercase tracking-widest text-muted-foreground mb-2">
                    Marking Result
                  </p>
                  <p className="text-base font-bold text-foreground">
                    {question.topic_tags?.[0]}
                  </p>
                </div>
                <div className={cn("text-5xl font-black drop-shadow-sm", scoreColor)}>
                  {result.score}
                  <span className="text-2xl font-bold text-muted-foreground ml-1">
                    /{result.max_score}
                  </span>
                </div>
              </div>
              
              <div className="bg-secondary/50 rounded-2xl p-6 mb-6 border-2 border-border/50">
                 <p className="text-lg font-medium text-foreground leading-relaxed italic">
                   "{result.feedback_summary}"
                 </p>
              </div>

              {result.correct_points.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm font-black uppercase tracking-widest text-green-600 mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" /> What you got right
                  </p>
                  <ul className="space-y-2">
                    {result.correct_points.map((p, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3 text-base font-medium text-green-800 bg-green-50 p-3 rounded-xl border-2 border-green-100"
                      >
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.missing_points.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm font-black uppercase tracking-widest text-red-600 mb-3 flex items-center gap-2">
                    <XCircle className="w-5 h-5" /> What you missed
                  </p>
                  <ul className="space-y-2">
                    {result.missing_points.map((p, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-3 text-base font-medium text-red-800 bg-red-50 p-3 rounded-xl border-2 border-red-100"
                      >
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.study_references.length > 0 && (
                <div className="mt-8 pt-6 border-t-2 border-border/50">
                  <p className="text-sm font-black uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                    <BookOpen className="w-5 h-5" /> Study References
                  </p>
                  <ul className="space-y-2">
                    {result.study_references.map((r, i) => (
                      <li key={i} className="text-sm font-bold text-primary bg-primary/10 p-3 rounded-xl border-2 border-primary/20 inline-block mr-2 mb-2">
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Global Bottom Check Bar */}
      {(status === "answering" || status === "submitting" || status === "reviewing") && (
          <div className="fixed bottom-0 inset-x-0 border-t-4 border-border bg-card p-4 sm:p-6 z-50 shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
              <div className="max-w-3xl mx-auto flex items-center justify-between">
                  <div className="hidden sm:block">
                      <p className="text-2xl font-black text-foreground tracking-tight">
                          {status === "reviewing" ? (pct >= 1 ? "Awesome job!" : pct >= 0.5 ? "Good effort!" : "Keep practicing!") : "Ready to submit?"}
                      </p>
                  </div>
                  
                  {status === "reviewing" ? (
                      <div className="flex gap-4 w-full sm:w-auto">
                          <Button
                              variant="outline"
                              size="lg"
                              className={cn(
                                  "gap-2 w-full sm:w-auto border-2 h-14 rounded-2xl font-bold text-base bg-card hover:bg-secondary text-foreground",
                                  flagged ? "text-orange-600 border-orange-300 bg-orange-50" : "border-border"
                              )}
                              onClick={flagAnswer}
                              disabled={flagged}
                          >
                              <Flag className="w-5 h-5" />
                              {flagged ? "Flagged" : "Report"}
                          </Button>
                          <Button
                              size="lg"
                              className="w-full sm:w-auto text-lg px-12 font-black uppercase tracking-widest h-14 rounded-2xl shadow-gamified active:translate-y-1 active:shadow-sm transition-all"
                              onClick={loadQuestion}
                          >
                              Continue
                          </Button>
                      </div>
                  ) : (
                      <Button
                          size="lg"
                          className="w-full sm:w-auto text-lg px-12 font-black uppercase tracking-widest h-14 rounded-2xl shadow-gamified active:translate-y-1 active:shadow-sm transition-all"
                          disabled={
                              status === "submitting" ||
                              !answer ||
                              (question?.question_type === "written" && answer.length < MIN_ANSWER_CHARS)
                          }
                          onClick={submitAnswer}
                      >
                          {status === "submitting" ? (
                              <>
                                  <Loader2 className="w-6 h-6 animate-spin mr-3" /> Marking...
                              </>
                          ) : (
                              "Check"
                          )}
                      </Button>
                  )}
              </div>
          </div>
      )}
    </div>
  );
}
