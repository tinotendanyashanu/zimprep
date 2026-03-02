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
    const fileInputRef = useRef<HTMLInputElement>(null);
    const attachments = useExamStore((state) => state.attachments[question?.id || ""] || []);
    const addAttachment = useExamStore((state) => state.addAttachment);
    const removeAttachment = useExamStore((state) => state.removeAttachment);
    
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

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || !e.target.files.length || !question) return;

        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onloadend = () => {
            if (reader.result) {
                addAttachment(question.id, reader.result as string);
            }
        };
        reader.readAsDataURL(file);
        
        // Reset input
        e.target.value = '';
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
                    <div className="flex items-center gap-4">
                         <span className={cn("transition-opacity text-xs", localValue.length > 0 ? "opacity-100 text-green-600" : "opacity-0")}>
                            Saving...
                        </span>
                        <button 
                            onClick={() => fileInputRef.current?.click()}
                            className="text-primary hover:text-primary/80 font-bold flex items-center gap-1"
                        >
                            + Upload Handwriting
                        </button>
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            className="hidden" 
                            accept="image/*"
                            onChange={handleFileSelect}
                        />
                    </div>
                </div>
                
                <textarea
                    className="flex-1 min-h-[300px] w-full resize-none p-6 pt-10 rounded-lg border border-zinc-300 focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none font-serif text-lg leading-relaxed bg-white shadow-inner text-zinc-800"
                    placeholder="Start writing your answer here..."
                    value={localValue}
                    onChange={handleChange}
                    spellCheck={false} // Exams usually don't have spellcheck, realism?
                />

                {/* Attachments Area */}
                {attachments.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                        {attachments.map((src, i) => (
                            <div key={i} className="relative group/image aspect-[3/4] rounded-lg overflow-hidden border border-zinc-200">
                                <img src={src} alt={`Handwriting ${i + 1}`} className="object-cover w-full h-full" />
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/image:opacity-100 transition-opacity flex items-center justify-center">
                                     <button 
                                        className="text-white bg-red-600 p-1 rounded-full px-3 text-xs font-bold"
                                        onClick={() => question && removeAttachment(question.id, i)}
                                    >
                                        Remove
                                     </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                
                <div className="mt-2 text-right text-xs text-zinc-400">
                    {localValue.split(/\s+/).filter(w => w.length > 0).length} words
                </div>
            </div>
        </div>
    );
}
