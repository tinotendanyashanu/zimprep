"use client";

import { useExamStore } from "@/lib/exam/store";
import { MOCK_PAPER } from "@/lib/exam/mock-data";
import { DashboardHeader } from "@/components/dashboard/header";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Clock, FileText, AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ExamPaper, Question } from "@/lib/exam/types";
import { getSubjectByName, findPaperId } from "@/lib/data";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
};

function buildFallbackPaper(subject: string, level: string, year: string, paperId: string): ExamPaper {
  return {
    ...MOCK_PAPER,
    id: `${subject}-${level}-${year}-${paperId}`,
    title: `${subject} — ${paperId.replace("-", " ").replace(/\b\w/g, (c) => c.toUpperCase())} (${year})`,
    subject,
    level: level as "Grade7" | "O" | "A",
    year: parseInt(year),
    paperNumber: parseInt(paperId.replace("paper-", "") || "1"),
  };
}

function mapApiQuestions(raw: Record<string, unknown>[]): Question[] {
  return raw.map((q) => ({
    id: q.id as string,
    questionNumber: q.question_number as string,
    text: q.text as string,
    marks: (q.marks as number) || 0,
    type: (q.question_type as string) === "mcq" ? "mcq" : "essay",
    has_image: !!(q.has_image),
    imageUrl: (q.image_url as string) || undefined,
    topic: ((q.topic_tags as string[]) || [])[0],
    mcqOptions: (() => {
      const mcqAnswers = q.mcq_answer as { correct_option?: string }[] | null;
      if (!mcqAnswers?.length) return undefined;
      return ["A", "B", "C", "D"].map((k) => ({ key: k as "A" | "B" | "C" | "D", text: k }));
    })(),
  }));
}

export default function ExamStartPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const initializeExam = useExamStore((state) => state.initializeExam);

  const subject = decodeURIComponent(params.subject as string);
  const paperId = params.paper as string;
  const level = searchParams.get("level") || "O";
  const year = searchParams.get("year") || "2023";
  const realPaperIdParam = searchParams.get("paper_id");

  const [paper, setPaper] = useState<ExamPaper | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        let realPaperId = realPaperIdParam;

        if (!realPaperId) {
          const subjectRecord = await getSubjectByName(subject);
          if (subjectRecord) {
            const paperNumber = parseInt(paperId.replace("paper-", "") || "1");
            realPaperId = await findPaperId(subjectRecord.id, parseInt(year), paperNumber);
          }
        }

        if (realPaperId) {
          const res = await fetch(`${API_URL}/catalog/papers/${realPaperId}`);
          if (res.ok) {
            const data = await res.json();
            const questions = mapApiQuestions((data.questions || []) as Record<string, unknown>[]);
            const examPaper: ExamPaper = {
              id: data.id,
              title: `${subject} — Paper ${data.paper_number} (${data.year})`,
              subject,
              level: (data.subject_level || level) as "Grade7" | "O" | "A",
              year: data.year,
              paperNumber: data.paper_number,
              durationMinutes: 90,
              totalMarks: questions.reduce((s, q) => s + q.marks, 0),
              instructions: [
                "Answer ALL questions.",
                "Write your answers in the spaces provided.",
                "Start each question on a new page.",
              ],
              questions,
            };
            setPaper(examPaper);
            setLoading(false);
            return;
          }
        }
      } catch {
        // fall through to demo mode
      }

      setPaper(buildFallbackPaper(subject, level, year, paperId));
      setIsDemo(true);
      setLoading(false);
    }

    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStart = () => {
    if (!paper) return;
    initializeExam(paper);
    const attemptId = `attempt-${Date.now()}`;
    router.push(`/exam/${attemptId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50/50 flex flex-col">
        <DashboardHeader title="Loading Paper…" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      </div>
    );
  }

  if (!paper) return null;

  return (
    <div className="min-h-screen bg-zinc-50/50 flex flex-col">
      <DashboardHeader title="Exam Instructions" />

      <main className="flex-1 max-w-3xl mx-auto w-full p-6 md:p-12 animate-in fade-in duration-500">
        <Link
          href={`/subjects/${encodeURIComponent(subject)}`}
          className="text-sm text-zinc-500 hover:text-zinc-900 flex items-center gap-1 mb-8"
        >
          <ArrowLeft className="w-4 h-4" /> Cancel & Go Back
        </Link>

        {isDemo && (
          <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm text-center">
            Demo mode — no real paper has been uploaded yet for this selection. Using sample questions.
          </div>
        )}

        <div className="bg-white border text-card-foreground shadow-sm rounded-xl overflow-hidden">
          <div className="p-8 border-b bg-zinc-50/50">
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              <span className="bg-zinc-900 text-white text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">Examination</span>
              <span className="text-xs font-medium text-zinc-500 uppercase tracking-widest">{subject}</span>
              <span className="text-xs font-medium text-zinc-400 uppercase tracking-widest">{LEVEL_LABELS[level] || level} · {year}</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 mb-2">{paper.title}</h1>
            <p className="text-zinc-500">Please read all instructions carefully before starting.</p>
          </div>

          <div className="p-8 space-y-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Duration", value: `${paper.durationMinutes}m`, icon: <Clock className="w-4 h-4 text-zinc-500" /> },
                { label: "Total Marks", value: String(paper.totalMarks), icon: <FileText className="w-4 h-4 text-zinc-500" /> },
                { label: "Level", value: LEVEL_LABELS[level] || level, icon: null },
                { label: "Questions", value: String(paper.questions.length), icon: null },
              ].map(({ label, value, icon }) => (
                <div key={label} className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
                  <div className="text-xs text-zinc-400 uppercase tracking-wider font-bold mb-1">{label}</div>
                  <div className="font-mono text-lg font-bold flex items-center gap-2">{icon}{value}</div>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <h3 className="font-bold text-lg border-b pb-2">Instructions to Candidates</h3>
              <ul className="space-y-3">
                {paper.instructions.map((inst, i) => (
                  <li key={i} className="flex gap-3 text-zinc-700 text-sm leading-relaxed">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-zinc-100 text-zinc-500 font-mono text-xs flex items-center justify-center border">{i + 1}</span>
                    {inst}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-4">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-sm text-amber-900">
                <p className="font-bold mb-1">Exam Mode Environment</p>
                <p>Once started, the timer begins. Your answers are auto-saved every 30 seconds. You may upload a photo of handwritten answers for each question.</p>
              </div>
            </div>

            <div className="pt-4">
              <Button onClick={handleStart} size="lg" className="w-full h-14 text-lg font-bold bg-zinc-900 hover:bg-zinc-800 shadow-xl shadow-zinc-200">
                Open Question Paper
              </Button>
              <p className="text-center text-xs text-zinc-400 mt-4">By clicking above, you confirm you have read the instructions and agree to examination rules.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
