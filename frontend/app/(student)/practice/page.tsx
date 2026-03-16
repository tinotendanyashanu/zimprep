"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";
import {
  getSubjects,
  getPracticeSession,
  getNextQuestion,
  getSubjectTopics,
  getWeakTopics,
  submitAttempt,
  flagAttempt,
  type Subject,
  type Question,
  type PracticeAttemptResult,
  type WeakTopic,
} from "@/lib/api";
import { UpgradePrompt } from "@/components/UpgradePrompt";
import { useQuota } from "@/hooks/useQuota";

// ── Types ─────────────────────────────────────────────────────────────────────

type Stage = "selecting-subject" | "practicing";

// ── Helpers ───────────────────────────────────────────────────────────────────

function groupByLevel(subjects: Subject[]): Record<string, Subject[]> {
  return subjects.reduce<Record<string, Subject[]>>((acc, s) => {
    (acc[s.level] ??= []).push(s);
    return acc;
  }, {});
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function PracticePage() {
  const { guardedSubmit, showUpgrade, upgradeDetail, dismissUpgrade } = useQuota();
  const [studentId, setStudentId] = useState<string | null>(null);

  // Subject selection
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(true);

  // Active practice state
  const [stage, setStage] = useState<Stage>("selecting-subject");
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState<string>("");
  const [result, setResult] = useState<PracticeAttemptResult | null>(null);
  const [weakTopics, setWeakTopics] = useState<WeakTopic[]>([]);

  // Session stats
  const [doneCount, setDoneCount] = useState(0);
  const [correctTotal, setCorrectTotal] = useState(0);
  const [maxTotal, setMaxTotal] = useState(0);
  const [streak, setStreak] = useState(0);

  // Loading / error
  const [questionLoading, setQuestionLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flagged, setFlagged] = useState(false);

  // Load student ID
  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data: { user } }) => {
        if (user) setStudentId(user.id);
      });
  }, []);

  // Load subjects
  useEffect(() => {
    getSubjects()
      .then(setSubjects)
      .catch(() => setError("Failed to load subjects"))
      .finally(() => setSubjectsLoading(false));
  }, []);

  // Refresh weak topics whenever the student submits an answer
  const refreshWeakTopics = useCallback(() => {
    if (!selectedSubject || !studentId) return;
    getWeakTopics(selectedSubject.id, studentId).then(setWeakTopics).catch(() => {});
  }, [selectedSubject, studentId]);

  // Fetch next question
  const fetchNextQuestion = useCallback(
    async (topic: string | null) => {
      if (!selectedSubject || !studentId) return;
      setQuestionLoading(true);
      setResult(null);
      setAnswer("");
      setFlagged(false);
      setError(null);
      try {
        const q = await getNextQuestion(selectedSubject.id, studentId, topic ?? undefined);
        setQuestion(q);
      } catch {
        setError("No more questions available for this filter.");
        setQuestion(null);
      } finally {
        setQuestionLoading(false);
      }
    },
    [selectedSubject, studentId],
  );

  // Select a subject → get/create practice session, load topics + first question
  async function selectSubject(subject: Subject) {
    if (!studentId) return;
    setError(null);
    setSelectedSubject(subject);
    setStage("practicing");
    setDoneCount(0);
    setCorrectTotal(0);
    setMaxTotal(0);
    setStreak(0);
    setActiveTopic(null);

    try {
      const [sessionRes, topicList] = await Promise.all([
        getPracticeSession(studentId, subject.id),
        getSubjectTopics(subject.id),
      ]);
      setSessionId(sessionRes.session_id);
      setTopics(topicList);
      // fetch first question
      setQuestionLoading(true);
      const q = await getNextQuestion(subject.id, studentId, undefined);
      setQuestion(q);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start practice session");
    } finally {
      setQuestionLoading(false);
    }
  }

  // Submit answer
  async function handleSubmit() {
    if (!sessionId || !question || !answer.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await guardedSubmit(() =>
        submitAttempt(sessionId, question.id, answer.trim()),
      );
      if (!res) return; // blocked by quota — UpgradePrompt shown
      setResult(res);
      setDoneCount((n) => n + 1);
      const score = res.ai_score ?? 0;
      setCorrectTotal((n) => n + score);
      setMaxTotal((n) => n + question.marks);
      setStreak((s) => (score > 0 ? s + 1 : 0));
      refreshWeakTopics();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  // Flag current result
  async function handleFlag() {
    if (!result) return;
    try {
      await flagAttempt(result.id);
      setFlagged(true);
    } catch {
      // silently ignore
    }
  }

  // Switch topic filter
  function handleTopicFilter(topic: string | null) {
    setActiveTopic(topic);
    fetchNextQuestion(topic);
    setResult(null);
    setAnswer("");
    setFlagged(false);
  }

  // ── Render: upgrade prompt (overlays any stage) ───────────────────────────────

  const upgradeOverlay = showUpgrade && upgradeDetail && (
    <UpgradePrompt detail={upgradeDetail} onDismiss={dismissUpgrade} />
  );

  // ── Render: subject selection ────────────────────────────────────────────────

  if (stage === "selecting-subject") {
    const grouped = groupByLevel(subjects);
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 space-y-8">
        {upgradeOverlay}
        <div>
          <h1 className="text-2xl font-semibold">Practice Mode</h1>
          <p className="text-muted-foreground mt-1">Choose a subject to start adaptive practice.</p>
        </div>

        {subjectsLoading && <p className="text-muted-foreground">Loading subjects…</p>}
        {error && <p className="text-destructive text-sm">{error}</p>}

        {Object.entries(grouped).map(([level, subs]) => (
          <div key={level} className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              {level}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {subs.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSubject(s)}
                  disabled={s.paper_count === 0}
                  className="text-left border rounded-lg px-4 py-3 hover:bg-accent transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <p className="font-medium">{s.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {s.paper_count} paper{s.paper_count !== 1 ? "s" : ""} available
                  </p>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // ── Render: practicing ───────────────────────────────────────────────────────

  const accuracy = maxTotal > 0 ? Math.round((correctTotal / maxTotal) * 100) : null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {upgradeOverlay}
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => {
            setStage("selecting-subject");
            setSelectedSubject(null);
            setSessionId(null);
            setQuestion(null);
            setResult(null);
            setWeakTopics([]);
            setTopics([]);
          }}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back
        </button>
        <h1 className="text-xl font-semibold">{selectedSubject?.name}</h1>
      </div>

      {/* Stats bar */}
      <div className="flex gap-6 text-sm mb-6 pb-4 border-b">
        <span>
          <span className="font-semibold">{doneCount}</span>{" "}
          <span className="text-muted-foreground">done</span>
        </span>
        {accuracy !== null && (
          <span>
            <span className="font-semibold">{accuracy}%</span>{" "}
            <span className="text-muted-foreground">accuracy</span>
          </span>
        )}
        {streak > 1 && (
          <span>
            <span className="font-semibold">{streak}</span>{" "}
            <span className="text-muted-foreground">streak</span>
          </span>
        )}
      </div>

      <div className="flex gap-6">
        {/* Main column */}
        <div className="flex-1 min-w-0 space-y-6">
          {/* Topic filter pills */}
          {topics.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
              <button
                onClick={() => handleTopicFilter(null)}
                className={`shrink-0 px-3 py-1 rounded-full text-sm border transition-colors ${
                  activeTopic === null
                    ? "bg-foreground text-background border-foreground"
                    : "hover:bg-accent border-border"
                }`}
              >
                All topics
              </button>
              {topics.map((t) => (
                <button
                  key={t}
                  onClick={() => handleTopicFilter(t)}
                  className={`shrink-0 px-3 py-1 rounded-full text-sm border transition-colors ${
                    activeTopic === t
                      ? "bg-foreground text-background border-foreground"
                      : "hover:bg-accent border-border"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          )}

          {/* Question card */}
          {questionLoading && (
            <div className="border rounded-xl p-6 text-muted-foreground">Loading question…</div>
          )}

          {error && !questionLoading && (
            <div className="border rounded-xl p-6 text-destructive text-sm">{error}</div>
          )}

          {question && !questionLoading && (
            <div className="border rounded-xl p-6 space-y-5">
              {/* Question meta */}
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  {question.topic_tags?.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {question.topic_tags.map((t) => (
                        <span
                          key={t}
                          className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="font-medium leading-relaxed">{question.text}</p>
                </div>
                <span className="shrink-0 text-sm text-muted-foreground whitespace-nowrap">
                  {question.marks} mark{question.marks !== 1 ? "s" : ""}
                </span>
              </div>

              {question.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={question.image_url}
                  alt="Question diagram"
                  className="max-w-full rounded border"
                />
              )}

              {/* Answer input */}
              {!result && (
                <>
                  {question.question_type === "mcq" ? (
                    <div className="space-y-2">
                      {(["A", "B", "C", "D"] as const).map((opt) => (
                        <label
                          key={opt}
                          className="flex items-center gap-3 cursor-pointer p-2 rounded-lg hover:bg-accent"
                        >
                          <input
                            type="radio"
                            name="mcq"
                            value={opt}
                            checked={answer === opt}
                            onChange={() => setAnswer(opt)}
                            className="accent-foreground"
                          />
                          <span className="font-medium">{opt}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <textarea
                      rows={5}
                      placeholder="Write your answer here…"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  )}

                  <Button
                    onClick={handleSubmit}
                    disabled={submitting || !answer.trim()}
                    className="w-full"
                  >
                    {submitting ? "Marking…" : "Submit Answer"}
                  </Button>
                </>
              )}

              {/* Inline feedback */}
              {result && (
                <div className="space-y-4 pt-2 border-t">
                  {/* Score badge */}
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-2xl font-bold ${
                        (result.ai_score ?? 0) >= question.marks * 0.7
                          ? "text-green-600"
                          : (result.ai_score ?? 0) >= question.marks * 0.4
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}
                    >
                      {result.ai_score ?? 0}/{question.marks}
                    </span>
                    <span className="text-sm text-muted-foreground">marks</span>
                  </div>

                  {result.ai_feedback && (
                    <div className="space-y-3 text-sm">
                      {result.ai_feedback.correct_points.length > 0 && (
                        <div>
                          <p className="font-medium text-green-700 dark:text-green-400 mb-1">
                            Correct points
                          </p>
                          <ul className="space-y-1 pl-4">
                            {result.ai_feedback.correct_points.map((p, i) => (
                              <li key={i} className="list-disc text-muted-foreground">
                                {p}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {result.ai_feedback.missing_points.length > 0 && (
                        <div>
                          <p className="font-medium text-red-700 dark:text-red-400 mb-1">
                            Missing points
                          </p>
                          <ul className="space-y-1 pl-4">
                            {result.ai_feedback.missing_points.map((p, i) => (
                              <li key={i} className="list-disc text-muted-foreground">
                                {p}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {result.ai_feedback.examiner_note && (
                        <div className="bg-muted rounded-lg px-4 py-3">
                          <p className="font-medium mb-0.5">Examiner note</p>
                          <p className="text-muted-foreground">{result.ai_feedback.examiner_note}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {result.ai_references && result.ai_references.length > 0 && (
                    <div className="text-sm">
                      <p className="font-medium mb-1">Study references</p>
                      <ul className="space-y-0.5 pl-4">
                        {result.ai_references.map((r, i) => (
                          <li key={i} className="list-disc text-muted-foreground">
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex gap-3 pt-1">
                    <Button
                      onClick={() => fetchNextQuestion(activeTopic)}
                      className="flex-1"
                    >
                      Next Question
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleFlag}
                      disabled={flagged}
                      className="text-sm"
                    >
                      {flagged ? "Flagged" : "Flag this marking"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Weak topics sidebar (desktop only) */}
        {weakTopics.length > 0 && (
          <aside className="hidden lg:block w-56 shrink-0">
            <p className="text-sm font-semibold mb-3">Weak Topics</p>
            <div className="space-y-3">
              {weakTopics.slice(0, 8).map((wt) => (
                <button
                  key={wt.topic}
                  onClick={() => handleTopicFilter(wt.topic)}
                  className="w-full text-left space-y-1 hover:opacity-80"
                >
                  <div className="flex justify-between text-xs">
                    <span className="truncate">{wt.topic}</span>
                    <span className="text-muted-foreground ml-1">
                      {Math.round(wt.fail_ratio * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-red-500 rounded-full"
                      style={{ width: `${Math.round(wt.fail_ratio * 100)}%` }}
                    />
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
