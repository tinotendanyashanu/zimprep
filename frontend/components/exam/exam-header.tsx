"use client";

import { useExamStore } from "@/lib/exam/store";
import { ExamTimer } from "./exam-timer";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";

export function ExamHeader({ onFinish }: { onFinish?: () => void }) {
    const paper = useExamStore((state) => state.paper);
    const submitExam = useExamStore((state) => state.submitExam);

    if (!paper) return null;

    const handleFinish = () => {
        if (onFinish) {
            onFinish();
        } else {
            submitExam();
        }
    };

    return (
        <header className="h-16 border-b bg-white flex items-center justify-between px-6 sticky top-0 z-10 w-full shrink-0">
            <div className="flex items-center gap-4">
                <div className="font-bold text-lg text-zinc-900 truncate max-w-md">
                    {paper.title}
                </div>
                <div className="h-6 w-px bg-zinc-200 hidden md:block" />
                <div className="text-sm text-zinc-500 hidden md:block">
                    {paper.subject}
                </div>
            </div>

            <div className="flex items-center gap-4">
                <ExamTimer />
                
                {/* Autosave Indicator (Mocked for now) */}
                <div className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-400">
                    <Save className="w-3 h-3" />
                    <span>Saved</span>
                </div>

                <Button variant="default" onClick={handleFinish} className="bg-zinc-900 hover:bg-zinc-800 text-white shadow-none">
                    Finish Exam
                </Button>
            </div>
        </header>
    );
}
