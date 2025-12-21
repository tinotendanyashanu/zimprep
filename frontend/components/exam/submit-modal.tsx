"use client";

import { useExamStore } from "@/lib/exam/store";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

// Simple custom modal since we might be missing the shadcn dialog component
export function SubmitModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const submitExam = useExamStore((state) => state.submitExam);
    const answers = useExamStore((state) => state.answers);
    const questions = useExamStore((state) => state.paper?.questions || []);
    const paper = useExamStore((state) => state.paper);

    const answeredCount = Object.keys(answers).length;
    const totalQuestions = questions.length;
    const unansweredCount = totalQuestions - answeredCount;

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in"
                onClick={onClose}
            />
            
            {/* Content */}
            <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
                <div className="flex flex-col items-center text-center">
                    <div className="h-12 w-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
                        <Lock className="h-6 w-6 text-red-600" />
                    </div>
                    
                    <h2 className="text-xl font-bold text-zinc-900 mb-2">
                        Submit Paper?
                    </h2>
                    
                    <p className="text-sm text-zinc-600 mb-6">
                        You are about to submit <strong>{paper?.title}</strong>. 
                        This action cannot be undone.
                    </p>

                    {unansweredCount > 0 && (
                        <div className="w-full bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-3 mb-6 text-left">
                            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                            <div className="text-sm text-amber-800">
                                <span className="font-bold">Warning:</span> You have {unansweredCount} unanswered questions.
                            </div>
                        </div>
                    )}

                    <div className="flex gap-3 w-full">
                        <Button variant="outline" className="flex-1" onClick={onClose}>
                            Keep Writing
                        </Button>
                        <Button 
                            className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                            onClick={() => {
                                submitExam();
                                onClose();
                            }}
                        >
                            Yes, Submit
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
