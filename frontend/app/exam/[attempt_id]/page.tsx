"use client";

import { AnswerEditor } from "@/components/exam/answer-editor";
import { ExamHeader } from "@/components/exam/exam-header";
import { QuestionList } from "@/components/exam/question-list";
import { SubmitModal } from "@/components/exam/submit-modal";
import { Button } from "@/components/ui/button";
import { useExamStore } from "@/lib/exam/store";
import { useEffect, useState } from "react";
import { CheckCircle2, Home, Loader2 } from "lucide-react";
import Link from "next/link";
import { ErrorState } from "@/components/system/ErrorState";

export default function ExamPage() {
    const status = useExamStore((state) => state.status);
    const paper = useExamStore((state) => state.paper);
    const isSubmitting = useExamStore((state) => state.isSubmitting);
    const submitError = useExamStore((state) => state.submitError);
    const restoreSession = useExamStore((state) => state.restoreSession);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [restored, setRestored] = useState(false);

    // On mount: try to restore an in-progress session from localStorage
    useEffect(() => {
        if (status === 'idle' && !paper) {
            restoreSession();
        }
        setRestored(true);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    if (!restored) {
        return (
            <div className="h-screen flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
        );
    }

    if (status === 'idle' && !paper) {
        return (
            <div className="h-screen flex items-center justify-center p-8 bg-zinc-50">
                <ErrorState
                    title="Session Not Found"
                    message="We couldn't retrieve your active exam session. It may have expired or you refreshed after submitting."
                    retryAction={() => (window.location.href = '/dashboard')}
                />
            </div>
        );
    }

    if (status === 'marking') {
        return (
            <div className="h-screen flex flex-col items-center justify-center p-8 text-center bg-zinc-50 animate-in fade-in">
                <div className="h-16 w-16 bg-zinc-100 text-zinc-600 rounded-full flex items-center justify-center mb-6">
                    <Loader2 className="h-8 w-8 animate-spin" />
                </div>
                <h1 className="text-2xl font-bold mb-2 text-zinc-900">Marking Your Paper</h1>
                <p className="text-zinc-500 max-w-md">
                    Claude AI is marking all {paper?.questions.length} questions using the Anthropic batch API.
                    This usually takes under a minute.
                </p>
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
                {submitError && (
                    <p className="text-red-600 text-sm mb-4 max-w-md bg-red-50 border border-red-200 rounded-lg p-3">
                        Marking error: {submitError}. Your answers are saved — results may be partial.
                    </p>
                )}
                <p className="text-zinc-500 mb-8 max-w-md">
                    Your answers for <strong>{paper?.title}</strong> have been securely recorded.
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
