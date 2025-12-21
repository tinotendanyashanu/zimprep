"use client";

import { AnswerEditor } from "@/components/exam/answer-editor";
import { ExamHeader } from "@/components/exam/exam-header";
import { QuestionList } from "@/components/exam/question-list";
import { SubmitModal } from "@/components/exam/submit-modal";
import { Button } from "@/components/ui/button";
import { useExamStore } from "@/lib/exam/store";
import { redirect } from "next/navigation";
import { useEffect, useState } from "react";
import { CheckCircle2, Home } from "lucide-react";
import Link from "next/link";
import { ErrorState } from "@/components/system/ErrorState";

export default function ExamPage() {
    const status = useExamStore((state) => state.status);
    const paper = useExamStore((state) => state.paper);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    
    // Subscribe to store submit status to open modal if triggered via header button,
    // actually header button calls submitExam directly which sets status to submitted?
    // No, header should probably trigger the modal first.
    // Let's modify Header to take an onFinish prop or just handle it here?
    // Ideally, the "Finish Exam" button in Header should open the modal.
    // But Header is a separate component. 
    // Let's make the store have a `requestSubmit` vs `confirmSubmit` or just handle it via prop drill or context?
    // Simpler: Just make the header button trigger a global store action or state that we listen to?
    // Actually, I can pass the setModalOpen to a Context, but that's overkill.
    // I'll make the Header button just call `submitExam`? No, that's final.
    // I'll leave the Header button logic for a moment.
    // Better: Make `ExamHeader` accept `onRequestSubmit`. 
    // Wait, `ExamHeader` is inside the layout of this page?
    // Yes. So I can pass a prop if I lift `ExamHeader` here.

    // BUT `ExamHeader` in my implementation imports `useExamStore` directly.
    // So if I want to trigger the modal from the header, I should probably:
    // 1. Add `isSubmitModalOpen` to the store? No, that's UI state.
    // 2. Just have Header emit nothing and let this page handle it?
    // Let's modify `ExamHeader` to NOT call `submitExam` but instead take a prop?
    // Or just import Header and wrap it?
    
    // DECISION: I will modify `ExamHeader` to accept an `onFinish` prop.
    
    // Safe guard: Redirect if no exam is running (e.g. refresh)
    useEffect(() => {
        if (status === 'idle' && !paper) {
            // In a real app we might try to restore session.
            // For now, redirect back to dashboard or show error.
            // redirect('/dashboard'); // Can't redirect synchronously in effect easily without flicker
        }
    }, [status, paper]);

    if (status === 'idle' && !paper) {
        return (
            <div className="h-screen flex items-center justify-center p-8 bg-zinc-50">
                <ErrorState 
                    title="Session Not Found"
                    message="We couldn't retrieve your active exam session. It may have expired."
                    retryAction={() => window.location.href = '/dashboard'}
                />
            </div>
        );
    }

    if (status === 'submitted') {
        return (
            <div className="h-screen flex flex-col items-center justify-center p-8 text-center bg-zinc-50 animate-in fade-in">
                <div className="h-16 w-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6">
                    <CheckCircle2 className="h-8 w-8" />
                </div>
                <h1 className="text-3xl font-bold mb-2 text-zinc-900">Exam Submitted</h1>
                <p className="text-zinc-500 mb-8 max-w-md">
                    Your answers for <strong>{paper?.title}</strong> have been securely recorded. 
                    Marking will begin shortly.
                </p>
                <Link href="/dashboard">
                    <Button size="lg" className="gap-2">
                        <Home className="w-4 h-4" /> Return Home
                    </Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-zinc-50 overflow-hidden">
            <ExamHeader onFinish={() => setIsSubmitModalOpen(true)} />
            
            <div className="flex-1 flex overflow-hidden">
                <QuestionList />
                
                <main className="flex-1 overflow-y-auto bg-white/50 relative">
                    <AnswerEditor />
                </main>
            </div>

            <SubmitModal 
                isOpen={isSubmitModalOpen} 
                onClose={() => setIsSubmitModalOpen(false)} 
            />
        </div>
    );
}
