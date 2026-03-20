"use client";

import { DashboardHeader } from "@/components/dashboard/header";
import { ArrowLeft, GraduationCap, Calendar, FileText } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";

type Level = "Grade7" | "O" | "A";
const LEVEL_LABELS: Record<Level, string> = {
    Grade7: "Grade 7",
    O: "O Level",
    A: "A Level",
};

const YEARS = [2024, 2023, 2022, 2021, 2020, 2019];
const PAPERS: Record<Level, { id: string; label: string; type: string; duration: string }[]> = {
    Grade7: [
        { id: "paper-1", label: "Paper 1", type: "Multiple Choice", duration: "2 hrs" },
        { id: "paper-2", label: "Paper 2", type: "Written", duration: "2 hrs" },
    ],
    O: [
        { id: "paper-1", label: "Paper 1", type: "Multiple Choice", duration: "1h 30m" },
        { id: "paper-2", label: "Paper 2", type: "Structured / Essay", duration: "2h 30m" },
    ],
    A: [
        { id: "paper-1", label: "Paper 1", type: "Structured", duration: "3 hrs" },
        { id: "paper-2", label: "Paper 2", type: "Essay", duration: "3 hrs" },
        { id: "paper-3", label: "Paper 3", type: "Coursework / Practical", duration: "3 hrs" },
    ],
};

function SelectionStep({
    label, done, value, onClick,
}: { label: string; done: boolean; value?: string; onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "flex items-center justify-between w-full px-5 py-4 rounded-xl border-2 text-left transition-all",
                done
                    ? "border-zinc-900 bg-zinc-900 text-white"
                    : "border-zinc-200 bg-white text-zinc-600 cursor-default opacity-70"
            )}
        >
            <span className="font-semibold">{label}</span>
            {done && value && <span className="text-sm font-bold text-zinc-300">{value}</span>}
        </button>
    );
}

export default function SubjectPage() {
    const params = useParams();
    const router = useRouter();
    const subject = decodeURIComponent(params.subject as string);

    const [level, setLevel] = useState<Level | null>(null);
    const [year, setYear] = useState<number | null>(null);

    return (
        <div className="min-h-screen bg-zinc-50/50">
            <DashboardHeader title={subject} />

            <main className="max-w-2xl mx-auto p-6 md:p-12 space-y-8 animate-in fade-in duration-500">
                <Link href="/dashboard" className="text-sm text-zinc-500 hover:text-zinc-900 flex items-center gap-1">
                    <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                </Link>

                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-1">{subject}</h1>
                    <p className="text-zinc-500">Select your level, year, and paper to begin.</p>
                </div>

                {/* Step 1 — Level */}
                <section className="space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                        <GraduationCap className="w-4 h-4" /> Step 1 — Select Level
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                        {(Object.keys(LEVEL_LABELS) as Level[]).map((l) => (
                            <button
                                key={l}
                                onClick={() => { setLevel(l); setYear(null); }}
                                className={cn(
                                    "py-3 rounded-xl border-2 text-sm font-semibold transition-all",
                                    level === l
                                        ? "border-zinc-900 bg-zinc-900 text-white"
                                        : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400"
                                )}
                            >
                                {LEVEL_LABELS[l]}
                            </button>
                        ))}
                    </div>
                </section>

                {/* Step 2 — Year */}
                {level && (
                    <section className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                            <Calendar className="w-4 h-4" /> Step 2 — Select Year
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            {YEARS.map((y) => (
                                <button
                                    key={y}
                                    onClick={() => setYear(y)}
                                    className={cn(
                                        "py-3 rounded-xl border-2 text-sm font-semibold transition-all",
                                        year === y
                                            ? "border-zinc-900 bg-zinc-900 text-white"
                                            : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400"
                                    )}
                                >
                                    {y}
                                </button>
                            ))}
                        </div>
                    </section>
                )}

                {/* Step 3 — Paper */}
                {level && year && (
                    <section className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                            <FileText className="w-4 h-4" /> Step 3 — Select Paper
                        </div>
                        <div className="space-y-3">
                            {PAPERS[level].map((p) => (
                                <button
                                    key={p.id}
                                    onClick={() =>
                                        router.push(
                                            `/subjects/${encodeURIComponent(subject)}/papers/${p.id}?level=${level}&year=${year}`
                                        )
                                    }
                                    className="w-full flex items-center justify-between p-4 rounded-xl border-2 border-zinc-200 bg-white hover:border-zinc-900 hover:bg-zinc-50 transition-all text-left group"
                                >
                                    <div>
                                        <div className="font-bold text-zinc-900">{p.label} — {year}</div>
                                        <div className="text-xs text-zinc-500 mt-0.5">{p.type} · {p.duration}</div>
                                    </div>
                                    <div className="text-xs font-medium text-zinc-400 group-hover:text-zinc-900 transition-colors">
                                        {LEVEL_LABELS[level]}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}
