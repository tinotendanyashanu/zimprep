"use client";

import { DashboardHeader } from "@/components/dashboard/header";
import { ArrowLeft, Book, Clock, PlayCircle } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const PAPER_TYPES: Record<string, { type: string; duration: string; description: string }> = {
    "paper-1": {
        type: "Multiple Choice / Structured",
        duration: "1h 30m",
        description: "First paper of the examination series, covering the core syllabus topics.",
    },
    "paper-2": {
        type: "Structured / Essay",
        duration: "2h 30m",
        description: "Second paper requiring detailed written responses and source analysis.",
    },
    "paper-3": {
        type: "Coursework / Practical",
        duration: "3h",
        description: "Third paper assessing practical skills or coursework-based tasks.",
    },
};

const LEVEL_LABELS: Record<string, string> = {
    Grade7: "Grade 7",
    O: "O Level",
    A: "A Level",
};

export default function PaperPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const router = useRouter();

    const subject = decodeURIComponent(params.subject as string);
    const paperId = params.paper as string;
    const level = searchParams.get("level") || "O";
    const year = searchParams.get("year") || "2023";

    const info = PAPER_TYPES[paperId] || {
        type: "Written",
        duration: "2h",
        description: "Standard examination paper.",
    };

    const paperName = paperId.replace("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());

    const startExam = () => {
        router.push(
            `/subjects/${encodeURIComponent(subject)}/papers/${paperId}/start?level=${level}&year=${year}`
        );
    };

    return (
        <div className="min-h-screen bg-zinc-50/50">
            <DashboardHeader title={`${paperName} — ${year}`} />

            <main className="max-w-4xl mx-auto p-6 md:p-12 space-y-8 animate-in fade-in duration-500">
                <Link
                    href={`/subjects/${encodeURIComponent(subject)}`}
                    className="text-sm font-medium text-zinc-500 hover:text-zinc-900 flex items-center gap-1"
                >
                    <ArrowLeft className="w-4 h-4" /> Back to {subject}
                </Link>

                <div className="grid md:grid-cols-3 gap-8">
                    {/* Paper Info */}
                    <div className="md:col-span-2 space-y-6">
                        <div>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="bg-zinc-900 text-white text-xs font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                                    {LEVEL_LABELS[level] || level}
                                </span>
                                <span className="text-xs text-zinc-400">{year}</span>
                            </div>
                            <h1 className="text-3xl font-bold tracking-tight mb-2">
                                {subject} — {paperName}
                            </h1>
                            <div className="flex items-center gap-4 text-sm text-zinc-500">
                                <span className="flex items-center gap-1.5 bg-zinc-100 px-2 py-1 rounded">
                                    <Clock className="w-3.5 h-3.5" /> {info.duration}
                                </span>
                                <span className="flex items-center gap-1.5 bg-zinc-100 px-2 py-1 rounded">
                                    <Book className="w-3.5 h-3.5" /> {info.type}
                                </span>
                            </div>
                        </div>
                        <div className="prose prose-zinc text-sm">
                            <p>{info.description}</p>
                            <p>
                                This exam includes typed and handwritten answer support.
                                Your answers are auto-saved to prevent data loss on connectivity issues.
                                MCQ questions are marked instantly via answer key lookup.
                            </p>
                        </div>
                    </div>

                    {/* Mode Selection */}
                    <div className="md:col-span-1 space-y-4">
                        <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider">Select Mode</h3>

                        <Card
                            className="p-4 hover:border-zinc-900 cursor-pointer transition-all border-l-4 border-l-zinc-900"
                            onClick={startExam}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-lg">Exam Mode</span>
                                <PlayCircle className="w-5 h-5 text-zinc-900" />
                            </div>
                            <p className="text-xs text-zinc-500 mb-3">Timed. Full simulation. AI-marked.</p>
                            <Button className="w-full h-8 text-xs font-bold" onClick={startExam}>
                                Start Exam
                            </Button>
                        </Card>

                        <Card
                            className="p-4 hover:border-blue-400 cursor-pointer transition-all border-l-4 border-l-blue-400 opacity-60"
                            onClick={() => alert("Practice Mode coming soon!")}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-lg">Practice Mode</span>
                                <Book className="w-5 h-5 text-blue-500" />
                            </div>
                            <p className="text-xs text-zinc-500 mb-3">Untimed. Instant per-question feedback.</p>
                            <Button variant="outline" className="w-full h-8 text-xs" disabled>
                                Coming Soon
                            </Button>
                        </Card>
                    </div>
                </div>
            </main>
        </div>
    );
}
