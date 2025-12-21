"use client";

import { useExamStore } from "@/lib/exam/store";
import { Clock } from "lucide-react";
import { useEffect, useMemo } from "react";

export function ExamTimer() {
    const timeLeft = useExamStore((state) => state.timeLeft);
    const tickTimer = useExamStore((state) => state.tickTimer);
    const status = useExamStore((state) => state.status);

    useEffect(() => {
        if (status !== 'running') return;

        const interval = setInterval(() => {
            tickTimer();
        }, 1000);

        return () => clearInterval(interval);
    }, [status, tickTimer]);

    const formattedTime = useMemo(() => {
        const hours = Math.floor(timeLeft / 3600);
        const minutes = Math.floor((timeLeft % 3600) / 60);
        const seconds = timeLeft % 60;

        const pad = (n: number) => n.toString().padStart(2, "0");
        return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }, [timeLeft]);

    // Color logic: < 5 mins = red, < 15 mins = yellow, else normal
    const timerColor = useMemo(() => {
        if (timeLeft < 5 * 60) return "text-red-600 bg-red-50 border-red-200";
        if (timeLeft < 15 * 60) return "text-amber-600 bg-amber-50 border-amber-200";
        return "text-zinc-700 bg-zinc-100 border-zinc-200";
    }, [timeLeft]);

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border text-sm font-mono font-medium transition-colors ${timerColor}`}>
            <Clock className="w-4 h-4" />
            <span>{formattedTime}</span>
        </div>
    );
}
