"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Question = {
  id: string;
  question_number: string;
  sub_question: string | null;
  section: string | null;
  marks: number;
  text: string;
  has_image: boolean;
  image_url: string | null;
  topic_tags: string[];
  question_type: string;
};

type EditState = {
  text: string;
  marks: string;
  topic_tags: string;
  question_type: string;
};

export default function QuestionsQAPage() {
  const { id: paperId } = useParams<{ id: string }>();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState>({
    text: "",
    marks: "",
    topic_tags: "",
    question_type: "written",
  });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (!paperId) return;
    fetch(`${BACKEND}/admin/papers/${paperId}/questions`)
      .then((r) => r.json())
      .then((data) => {
        setQuestions(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [paperId]);

  function startEdit(q: Question) {
    setEditingId(q.id);
    setEditState({
      text: q.text,
      marks: String(q.marks),
      topic_tags: q.topic_tags.join(", "),
      question_type: q.question_type,
    });
    setSaveError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setSaveError(null);
  }

  async function saveEdit(questionId: string) {
    setSaving(true);
    setSaveError(null);

    const payload = {
      text: editState.text.trim(),
      marks: parseInt(editState.marks, 10),
      topic_tags: editState.topic_tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      question_type: editState.question_type,
    };

    try {
      const res = await fetch(`${BACKEND}/admin/questions/${questionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Save failed (${res.status})`);
      }
      const updated = await res.json();
      setQuestions((prev) => prev.map((q) => (q.id === questionId ? { ...q, ...updated } : q)));
      setEditingId(null);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted-foreground text-sm">Loading questions…</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <a
            href="/admin/papers"
            className="text-sm text-muted-foreground hover:text-foreground transition"
          >
            ← Back to Papers
          </a>
        </div>

        <div>
          <h1 className="text-2xl font-semibold text-foreground">Question QA Review</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {questions.length} question{questions.length !== 1 ? "s" : ""} extracted
          </p>
        </div>

        {questions.length === 0 ? (
          <div className="bg-card border border-border rounded-2xl p-6">
            <p className="text-sm text-muted-foreground">
              No questions found. The extraction may still be running — come back shortly.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {questions.map((q) => (
              <div
                key={q.id}
                className="bg-card border border-border rounded-2xl p-5"
              >
                {editingId === q.id ? (
                  /* Edit mode */
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm text-muted-foreground mb-2">
                      <span className="font-mono font-medium text-foreground">
                        Q{q.question_number}
                        {q.sub_question ? `(${q.sub_question})` : ""}
                      </span>
                      {q.section && <span>Section {q.section}</span>}
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-foreground mb-1">
                        Question Text
                      </label>
                      <textarea
                        rows={4}
                        value={editState.text}
                        onChange={(e) =>
                          setEditState((s) => ({ ...s, text: e.target.value }))
                        }
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
                      />
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-foreground mb-1">
                          Marks
                        </label>
                        <input
                          type="number"
                          min={0}
                          value={editState.marks}
                          onChange={(e) =>
                            setEditState((s) => ({ ...s, marks: e.target.value }))
                          }
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-foreground mb-1">
                          Type
                        </label>
                        <select
                          value={editState.question_type}
                          onChange={(e) =>
                            setEditState((s) => ({ ...s, question_type: e.target.value }))
                          }
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        >
                          <option value="written">Written</option>
                          <option value="mcq">MCQ</option>
                        </select>
                      </div>

                      <div className="sm:col-span-1 col-span-2">
                        <label className="block text-xs font-medium text-foreground mb-1">
                          Topic Tags (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={editState.topic_tags}
                          onChange={(e) =>
                            setEditState((s) => ({ ...s, topic_tags: e.target.value }))
                          }
                          placeholder="Algebra, Quadratics"
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>
                    </div>

                    {saveError && (
                      <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                        {saveError}
                      </p>
                    )}

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => saveEdit(q.id)}
                        disabled={saving}
                        className="px-4 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
                      >
                        {saving ? "Saving…" : "Save"}
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="px-4 py-1.5 border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  /* View mode */
                  <div>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2 flex-wrap">
                          <span className="font-mono font-semibold text-foreground text-sm">
                            Q{q.question_number}
                            {q.sub_question ? `(${q.sub_question})` : ""}
                          </span>
                          {q.section && (
                            <span className="bg-secondary px-1.5 py-0.5 rounded text-foreground">
                              Section {q.section}
                            </span>
                          )}
                          <span className="bg-secondary px-1.5 py-0.5 rounded text-foreground">
                            {q.marks} mark{q.marks !== 1 ? "s" : ""}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded border text-xs font-medium ${
                              q.question_type === "mcq"
                                ? "bg-blue-50 text-blue-700 border-blue-200"
                                : "bg-purple-50 text-purple-700 border-purple-200"
                            }`}
                          >
                            {q.question_type}
                          </span>
                          {q.has_image && (
                            <span className="bg-orange-50 text-orange-700 border border-orange-200 px-1.5 py-0.5 rounded text-xs">
                              has image
                            </span>
                          )}
                        </div>

                        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                          {q.text}
                        </p>

                        {q.topic_tags.length > 0 && (
                          <div className="flex items-center gap-1.5 mt-3 flex-wrap">
                            {q.topic_tags.map((tag) => (
                              <span
                                key={tag}
                                className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <button
                        onClick={() => startEdit(q)}
                        className="flex-shrink-0 text-xs text-primary font-medium hover:underline"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
    </div>
  );
}
