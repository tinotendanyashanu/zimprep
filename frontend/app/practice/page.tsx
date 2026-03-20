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
    <div className="grid grid-cols-2 gap-3">
      {["A", "B", "C", "D"].map((opt) => (
        <label
          key={opt}
          className={cn(
            "flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all",
            value === opt
              ? "border-zinc-900 bg-zinc-900 text-white"
              : "border-zinc-200 bg-white hover:border-zinc-400"
          )}
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
              "w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-sm flex-shrink-0",
              value === opt
                ? "border-white text-white"
                : "border-zinc-400 text-zinc-600"
            )}
          >
            {opt}
          </span>
          <span
            className={cn(
              "font-medium",
              value === opt ? "text-white" : "text-zinc-700"
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
    <div className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="h-14 border-b bg-white flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-900 text-sm"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
          <span className="text-sm font-semibold text-zinc-900">
            {subjectName} — Practice Mode
          </span>
        </div>
        <div className="flex items-center gap-4">
          {sessionMax > 0 && (
            <span className="text-sm text-zinc-500">
              Session:{" "}
              <span className="font-bold text-zinc-900">
                {sessionScore}/{sessionMax}
              </span>{" "}
              ({questionCount} questions)
            </span>
          )}
          {/* Topic filter */}
          {allTopics.length > 0 && (
            <select
              value={topicFilter}
              onChange={(e) => setTopicFilter(e.target.value)}
              className="text-xs border border-zinc-200 rounded-md px-2 py-1 bg-white text-zinc-700"
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

      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
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
            <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-start justify-between mb-4 pb-4 border-b border-zinc-100">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                    Question {question.question_number}
                  </span>
                  {question.topic_tags?.[0] && (
                    <span className="ml-2 text-xs text-zinc-400">
                      — {question.topic_tags[0]}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {question.question_type === "mcq" && (
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">
                      MCQ
                    </span>
                  )}
                  <span className="bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded text-xs font-medium">
                    {question.marks} {question.marks === 1 ? "Mark" : "Marks"}
                  </span>
                </div>
              </div>
              {question.has_image && question.image_url && (
                <div className="mb-4 rounded-md overflow-hidden border border-zinc-200">
                  <img
                    src={question.image_url}
                    alt="Question diagram"
                    className="max-w-full object-contain max-h-64 mx-auto block"
                  />
                </div>
              )}
              <div
                className="prose prose-zinc max-w-none prose-p:leading-relaxed"
                dangerouslySetInnerHTML={{ __html: question.text }}
              />
            </div>

            <div className="bg-white border border-zinc-200 rounded-xl p-6 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4">
                Your Answer
              </p>
              {question.question_type === "mcq" ? (
                <MCQSimple value={answer} onChange={setAnswer} />
              ) : (
                <div className="space-y-2">
                  <textarea
                    className="w-full min-h-[180px] p-4 border border-zinc-200 rounded-lg font-serif text-base leading-relaxed focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none resize-none"
                    placeholder="Write your answer here…"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    disabled={status === "submitting"}
                  />
                  <div className="flex justify-between text-xs text-zinc-400">
                    <span
                      className={cn(
                        answer.length > 0 && answer.length < MIN_ANSWER_CHARS
                          ? "text-amber-500"
                          : ""
                      )}
                    >
                      {answer.length > 0 && answer.length < MIN_ANSWER_CHARS
                        ? `Min. ${MIN_ANSWER_CHARS} characters required (${answer.length}/${MIN_ANSWER_CHARS})`
                        : `${answer.split(/\s+/).filter(Boolean).length} words`}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <Button
              className="w-full bg-zinc-900 hover:bg-zinc-800 text-white gap-2"
              disabled={
                status === "submitting" ||
                !answer ||
                (question.question_type === "written" &&
                  answer.length < MIN_ANSWER_CHARS)
              }
              onClick={submitAnswer}
            >
              {status === "submitting" ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Claude is
                  marking…
                </>
              ) : (
                <>
                  Mark This Answer <ChevronRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </>
        )}

        {/* Reviewing */}
        {status === "reviewing" && question && result && (
          <>
            <div
              className={cn(
                "bg-white border-2 rounded-xl p-6 shadow-sm",
                pct >= 1
                  ? "border-green-200"
                  : pct >= 0.5
                  ? "border-amber-200"
                  : "border-red-200"
              )}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-1">
                    Question {question.question_number}
                  </p>
                  <p className="text-sm text-zinc-600">
                    {question.topic_tags?.[0]}
                  </p>
                </div>
                <div className={cn("text-3xl font-black", scoreColor)}>
                  {result.score}
                  <span className="text-lg font-medium text-zinc-400">
                    /{result.max_score}
                  </span>
                </div>
              </div>
              <p className="text-sm text-zinc-700 leading-relaxed mb-4 italic border-l-4 border-zinc-200 pl-4">
                {result.feedback_summary}
              </p>
              {result.correct_points.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-green-700 mb-2">
                    Correct
                  </p>
                  <ul className="space-y-1">
                    {result.correct_points.map((p, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-green-800"
                      >
                        <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-green-500" />{" "}
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.missing_points.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-red-700 mb-2">
                    Missing
                  </p>
                  <ul className="space-y-1">
                    {result.missing_points.map((p, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-red-800"
                      >
                        <XCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />{" "}
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.study_references.length > 0 && (
                <div className="mt-4 pt-4 border-t border-zinc-100">
                  <p className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2 flex items-center gap-1">
                    <BookOpen className="w-3 h-3" /> Study References
                  </p>
                  <ul className="space-y-0.5">
                    {result.study_references.map((r, i) => (
                      <li key={i} className="text-xs text-zinc-500">
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                className={cn(
                  "gap-2 text-zinc-500",
                  flagged && "text-amber-600 border-amber-300 bg-amber-50"
                )}
                onClick={flagAnswer}
                disabled={flagged}
              >
                <Flag className="w-4 h-4" />
                {flagged ? "Flagged for Review" : "Flag Incorrect Marking"}
              </Button>
              <Button
                className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white gap-2"
                onClick={loadQuestion}
              >
                Next Question <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
