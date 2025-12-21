"use client";

import { useExamStore } from "@/lib/exam/store";
import { getMockPaper, MOCK_PAPER } from "@/lib/exam/mock-data";
import { DashboardHeader } from "@/components/dashboard/header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Clock, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function ExamStartPage() {
    const params = useParams();
    const router = useRouter();
    const initializeExam = useExamStore((state) => state.initializeExam);
    
    // In a real app, we'd fetch the specific paper based on params
    // For Phase 3, we use the rich MOCK_PAPER to ensure the writing interface works perfectly
    const paper = MOCK_PAPER; 
    
    const subject = decodeURIComponent(params.subject as string);
    const paperId = params.paper as string;

    const handleStart = () => {
        // Initialize the store
        initializeExam(paper);
        
        // Generate a mock attempt ID
        const attemptId = `attempt-${Date.now()}`;
        
        // Navigate to the secure exam interface
        router.push(`/exam/${attemptId}`);
    };

    return (
        <div className="min-h-screen bg-zinc-50/50 flex flex-col">
            <DashboardHeader title="Exam Instructions" />

            <main className="flex-1 max-w-3xl mx-auto w-full p-6 md:p-12 animate-in fade-in duration-500">
                <Link href={`/subjects/${encodeURIComponent(subject)}/papers/${paperId}`} className="text-sm text-zinc-500 hover:text-zinc-900 flex items-center gap-1 mb-8">
                    <ArrowLeft className="w-4 h-4" /> Cancel & Go Back
                </Link>

                <div className="bg-white border text-card-foreground shadow-sm rounded-xl overflow-hidden">
                    <div className="p-8 border-b bg-zinc-50/50">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="bg-zinc-900 text-white text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">
                                Examination
                            </span>
                            <span className="text-xs font-medium text-zinc-500 uppercase tracking-widest">
                                {subject}
                            </span>
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 mb-2">
                            {paper.title}
                        </h1>
                        <p className="text-zinc-500">
                            Please read the instructions carefully before starting.
                        </p>
                    </div>

                    <div className="p-8 space-y-8">
                        {/* Key Info Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
                                <div className="text-xs text-zinc-400 uppercase tracking-wider font-bold mb-1">Duration</div>
                                <div className="font-mono text-lg font-bold flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-zinc-500" />
                                    {paper.durationMinutes}m
                                </div>
                            </div>
                             <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100">
                                <div className="text-xs text-zinc-400 uppercase tracking-wider font-bold mb-1">Marks</div>
                                <div className="font-mono text-lg font-bold flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-zinc-500" />
                                    {paper.totalMarks}
                                </div>
                            </div>
                             <div className="p-4 bg-zinc-50 rounded-lg border border-zinc-100 col-span-2">
                                <div className="text-xs text-zinc-400 uppercase tracking-wider font-bold mb-1">Format</div>
                                <div className="text-sm font-medium">Standard Written Exam</div>
                            </div>
                        </div>

                        {/* Rules / Instructions */}
                        <div className="space-y-4">
                            <h3 className="font-bold text-lg border-b pb-2">Instructions to Candidates</h3>
                            <ul className="space-y-3">
                                {paper.instructions.map((inst, i) => (
                                    <li key={i} className="flex gap-3 text-zinc-700 text-sm leading-relaxed">
                                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-zinc-100 text-zinc-500 font-mono text-xs flex items-center justify-center border">
                                            {i + 1}
                                        </span>
                                        {inst}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Warning Box */}
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-4">
                            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                            <div className="text-sm text-amber-900">
                                <p className="font-bold mb-1">Exam Mode Environment</p>
                                <p>
                                    Once you start, the timer will begin. 
                                    Do not close the browser window or the exam will be terminated.
                                    Ensure you have a stable connection.
                                </p>
                            </div>
                        </div>

                        {/* Action */}
                        <div className="pt-4">
                            <Button 
                                onClick={handleStart} 
                                size="lg" 
                                className="w-full h-14 text-lg font-bold bg-zinc-900 hover:bg-zinc-800 shadow-xl shadow-zinc-200"
                            >
                                Open Question Paper
                            </Button>
                            <p className="text-center text-xs text-zinc-400 mt-4">
                                By clicking above, you agree to the examination rules.
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
