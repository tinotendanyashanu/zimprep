"use client";

import { useExamStore } from "@/lib/exam/store";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

export function AnswerEditor() {
    const questions = useExamStore((state) => state.paper?.questions);
    const currentQuestionIndex = useExamStore((state) => state.currentQuestionIndex);
    const setAnswer = useExamStore((state) => state.setAnswer);
    const answers = useExamStore((state) => state.answers);

    const question = questions?.[currentQuestionIndex];
    
    // Local state for the textarea to avoid excessive rerenders on every keystroke if we wanted,
    // but hooking directly to store is fine for < 1000ms updates usually. 
    // For large text, local state + debounce is better. Let's start direct for simplicity.
    // Actually, controlled input with Zustand might be laggy for fast typists. 
    // Let's use local state and sync on blur or effect.
    
    const [localValue, setLocalValue] = useState("");
    
    // Sync when question changes
    useEffect(() => {
        if (question) {
            setLocalValue(answers[question.id] || "");
        }
    }, [question, answers]);

    // Save to store when localValue changes (debounced effect can be added here)
    // For now, let's just save on blur or valid change
    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        setLocalValue(val);
        if (question) {
            setAnswer(question.id, val);
        }
    };

    if (!question) return <div className="p-8 text-center text-zinc-400">Loading question...</div>;

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto w-full">
            {/* Question Display Area */}
            <div className="mb-6 p-6 bg-white border border-zinc-200 rounded-lg shadow-sm">
                <div className="flex justify-between items-start mb-4 border-b border-zinc-100 pb-4">
                    <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest">
                        Question {currentQuestionIndex + 1}
                    </h2>
                    <span className="bg-zinc-100 text-zinc-600 px-2 py-1 rounded text-xs font-medium">
                        {question.marks} Marks
                    </span>
                </div>
                
                <div 
                    className="prose prose-zinc max-w-none prose-p:leading-relaxed prose-headings:font-bold"
                    dangerouslySetInnerHTML={{ __html: question.text }} 
                />
            </div>

            {/* Answer Input Area */}
            <div className="flex-1 flex flex-col relative group">
                <div className="absolute top-0 left-0 right-0 bg-zinc-100/50 border-b px-4 py-2 text-xs text-zinc-500 font-medium flex justify-between items-center z-10 rounded-t-lg border-zinc-200 border-l border-r border-t">
                    <span>Your Answer</span>
                    <span className={cn("transition-opacity", localValue.length > 0 ? "opacity-100 text-green-600" : "opacity-0")}>
                        Saving...
                    </span>
                </div>
                <textarea
                    className="flex-1 min-h-[400px] w-full resize-none p-6 pt-10 rounded-lg border border-zinc-300 focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none font-serif text-lg leading-relaxed bg-white shadow-inner text-zinc-800"
                    placeholder="Start writing your answer here..."
                    value={localValue}
                    onChange={handleChange}
                    spellCheck={false} // Exams usually don't have spellcheck, realism?
                />
                
                <div className="mt-2 text-right text-xs text-zinc-400">
                    {localValue.split(/\s+/).filter(w => w.length > 0).length} words
                </div>
            </div>
        </div>
    );
}
