"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  adminListPaperQuestions,
  adminPatchQuestion,
  adminDeleteQuestion,
  AdminQuestion,
  AdminQuestionPatch,
} from "@/lib/api-client";
import { LoadingState } from "@/components/system/LoadingState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CheckCircle,
  XCircle,
  Pencil,
  Save,
  X,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

type Tab = "pending" | "approved" | "rejected" | "all";

// ---------------------------------------------------------------------------
// Question card
// ---------------------------------------------------------------------------

function QuestionCard({
  q,
  onUpdate,
  onDelete,
}: {
  q: AdminQuestion;
  onUpdate: (id: string, patch: AdminQuestionPatch) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [saving, setSaving] = useState(false);

  // Editable fields
  const [text, setText] = useState(q.text);
  const [marks, setMarks] = useState(q.marks.toString());
  const [qType, setQType] = useState<"written" | "mcq">(q.question_type);
  const [tags, setTags] = useState(q.topic_tags.join(", "));
  const [mcqAnswer, setMcqAnswer] = useState<string>(
    q.mcq_answer?.[0]?.correct_option ?? ""
  );

  const handleApprove = async () => {
    setSaving(true);
    try {
      await onUpdate(q.id, { qa_status: "approved" });
    } finally {
      setSaving(false);
    }
  };

  const handleReject = async () => {
    setSaving(true);
    try {
      await onDelete(q.id);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const patch: AdminQuestionPatch = {
        text,
        marks: parseInt(marks) || 0,
        question_type: qType,
        topic_tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      };
      if (qType === "mcq" && mcqAnswer) {
        patch.mcq_correct_option = mcqAnswer as "A" | "B" | "C" | "D";
      }
      await onUpdate(q.id, patch);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const statusColor = {
    pending: "border-l-amber-400",
    approved: "border-l-emerald-400",
    rejected: "border-l-red-400",
  }[q.qa_status];

  return (
    <div
      className={cn(
        "bg-white border border-zinc-200 rounded-xl border-l-4 overflow-hidden",
        statusColor
      )}
    >
      {/* Header */}
      <div
        className="flex items-start justify-between p-4 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xs font-bold text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded shrink-0">
            Q{q.question_number}
            {q.sub_question && `.${q.sub_question}`}
          </span>
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded-full font-medium shrink-0",
              q.question_type === "mcq"
                ? "bg-blue-50 text-blue-700 border border-blue-200"
                : "bg-zinc-50 text-zinc-700 border border-zinc-200"
            )}
          >
            {q.question_type.toUpperCase()}
          </span>
          <span className="text-xs text-zinc-400 shrink-0">{q.marks} mark{q.marks !== 1 ? "s" : ""}</span>
          {q.has_image && (
            <span className="text-xs text-purple-600 flex items-center gap-0.5 shrink-0">
              <ImageIcon className="w-3 h-3" /> image
            </span>
          )}
          <p className="text-sm text-zinc-700 truncate">{q.text.slice(0, 80)}</p>
        </div>
        <div className="shrink-0 ml-2">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-zinc-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-zinc-400" />
          )}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-zinc-100 p-4 space-y-4">
          {editing ? (
            /* Edit mode */
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Question Text</Label>
                <textarea
                  className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 min-h-[100px]"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Marks</Label>
                  <Input
                    type="number"
                    min={0}
                    value={marks}
                    onChange={(e) => setMarks(e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Type</Label>
                  <select
                    value={qType}
                    onChange={(e) => setQType(e.target.value as "written" | "mcq")}
                    className="w-full h-8 rounded-md border border-zinc-200 bg-white px-2 text-sm focus:outline-none"
                  >
                    <option value="written">Written</option>
                    <option value="mcq">MCQ</option>
                  </select>
                </div>
                {qType === "mcq" && (
                  <div className="space-y-1.5">
                    <Label className="text-xs">Correct Answer</Label>
                    <select
                      value={mcqAnswer}
                      onChange={(e) => setMcqAnswer(e.target.value)}
                      className="w-full h-8 rounded-md border border-zinc-200 bg-white px-2 text-sm focus:outline-none"
                    >
                      <option value="">Select…</option>
                      {["A", "B", "C", "D"].map((o) => (
                        <option key={o} value={o}>
                          {o}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Topic Tags (comma-separated)</Label>
                <Input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="e.g. algebra, quadratic equations"
                  className="h-8 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSave} disabled={saving}>
                  <Save className="w-3.5 h-3.5 mr-1.5" />
                  {saving ? "Saving…" : "Save Changes"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditing(false)}
                  disabled={saving}
                >
                  <X className="w-3.5 h-3.5 mr-1.5" />
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            /* View mode */
            <div className="space-y-3">
              <p className="text-sm text-zinc-800 whitespace-pre-wrap leading-relaxed">{q.text}</p>

              {q.mcq_answer && q.mcq_answer.length > 0 && (
                <p className="text-xs text-blue-600 bg-blue-50 border border-blue-100 rounded px-2 py-1 inline-block">
                  Correct answer: <strong>{q.mcq_answer[0].correct_option}</strong>
                </p>
              )}

              {q.topic_tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {q.topic_tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-xs bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {q.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={q.image_url}
                  alt="Question diagram"
                  className="max-w-sm rounded border border-zinc-200 mt-2"
                />
              )}
            </div>
          )}

          {/* Actions */}
          {!editing && q.qa_status === "pending" && (
            <div className="flex gap-2 pt-2 border-t border-zinc-100">
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={handleApprove}
                disabled={saving}
              >
                <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setEditing(true)}
              >
                <Pencil className="w-3.5 h-3.5 mr-1.5" />
                Edit
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-red-600 hover:bg-red-50 hover:border-red-300"
                onClick={handleReject}
                disabled={saving}
              >
                <XCircle className="w-3.5 h-3.5 mr-1.5" />
                Reject
              </Button>
            </div>
          )}

          {!editing && q.qa_status === "approved" && (
            <div className="flex gap-2 pt-2 border-t border-zinc-100">
              <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="w-3.5 h-3.5 mr-1.5" />
                Edit
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-red-600 hover:bg-red-50 hover:border-red-300"
                onClick={handleReject}
                disabled={saving}
              >
                <XCircle className="w-3.5 h-3.5 mr-1.5" />
                Remove
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function PaperQAPage() {
  const params = useParams();
  const paperId = params.paper_id as string;

  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("pending");

  useEffect(() => {
    setLoading(true);
    setError(null);
    adminListPaperQuestions(paperId, tab === "all" ? undefined : tab)
      .then(setQuestions)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tab, paperId]);

  const handleUpdate = async (id: string, patch: AdminQuestionPatch) => {
    await adminPatchQuestion(id, patch);
    setQuestions((prev) =>
      prev.map((q) =>
        q.id === id
          ? { ...q, ...patch, mcq_answer: patch.mcq_correct_option ? [{ id: q.mcq_answer?.[0]?.id ?? "", correct_option: patch.mcq_correct_option }] : q.mcq_answer }
          : q
      ).filter((q) => tab !== "all" ? q.qa_status === tab : true)
    );
  };

  const handleDelete = async (id: string) => {
    await adminDeleteQuestion(id);
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const TABS: { key: Tab; label: string }[] = [
    { key: "pending", label: "Pending" },
    { key: "approved", label: "Approved" },
    { key: "rejected", label: "Rejected" },
    { key: "all", label: "All" },
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">QA Review</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Review, edit, and approve extracted questions before they go live.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-100 p-1 rounded-lg w-fit">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
              tab === key
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-500 hover:text-zinc-700"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState variant="spinner" text="Loading questions..." />
      ) : error ? (
        <p className="text-red-500 text-sm">{error}</p>
      ) : questions.length === 0 ? (
        <div className="bg-white border border-dashed border-zinc-200 rounded-xl p-12 text-center text-zinc-400">
          No {tab !== "all" ? tab : ""} questions found.
        </div>
      ) : (
        <div className="space-y-3">
          {tab === "pending" && questions.length > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-500">
                <strong className="text-zinc-900">{questions.length}</strong> question{questions.length !== 1 ? "s" : ""} pending review
              </p>
              <Button
                size="sm"
                variant="outline"
                className="text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                onClick={async () => {
                  for (const q of questions) {
                    await adminPatchQuestion(q.id, { qa_status: "approved" });
                  }
                  setQuestions([]);
                }}
              >
                <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                Approve All
              </Button>
            </div>
          )}

          {questions.map((q) => (
            <QuestionCard
              key={q.id}
              q={q}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
