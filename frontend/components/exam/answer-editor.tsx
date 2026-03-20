"use client";

import { useExamStore } from "@/lib/exam/store";
import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Camera, Keyboard, Loader2, CheckCircle2, AlertCircle, ChevronLeft, ChevronRight, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Client-side image compression (target < 1 MB)
// ---------------------------------------------------------------------------
async function compressImage(file: File, maxBytes = 900 * 1024): Promise<{ blob: Blob; dataUrl: string }> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = (e) => {
            const img = new window.Image();
            img.onerror = reject;
            img.onload = () => {
                let { width, height } = img;
                let quality = 0.82;

                const canvas = document.createElement("canvas");
                const ctx = canvas.getContext("2d")!;

                const tryCompress = (): { blob: Blob; dataUrl: string } | null => {
                    canvas.width = width;
                    canvas.height = height;
                    ctx.clearRect(0, 0, width, height);
                    ctx.drawImage(img, 0, 0, width, height);
                    const dataUrl = canvas.toDataURL("image/jpeg", quality);
                    // Estimate byte size: base64 overhead ~1.37x
                    const estimatedBytes = (dataUrl.length * 3) / 4;
                    if (estimatedBytes <= maxBytes || (width <= 600 && quality <= 0.4)) {
                        // Convert dataUrl to Blob
                        const byteStr = atob(dataUrl.split(",")[1]);
                        const arr = new Uint8Array(byteStr.length);
                        for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i);
                        return { blob: new Blob([arr], { type: "image/jpeg" }), dataUrl };
                    }
                    return null;
                };

                // Iterative reduction
                for (let attempt = 0; attempt < 10; attempt++) {
                    const result = tryCompress();
                    if (result) { resolve(result); return; }
                    if (quality > 0.42) {
                        quality -= 0.1;
                    } else {
                        width = Math.floor(width * 0.75);
                        height = Math.floor(height * 0.75);
                        quality = 0.72;
                    }
                }
                // Final attempt
                const r = tryCompress();
                if (r) resolve(r);
                else reject(new Error("Could not compress image below 1 MB."));
            };
            img.src = e.target!.result as string;
        };
        reader.readAsDataURL(file);
    });
}

// ---------------------------------------------------------------------------
// MCQ option row
// ---------------------------------------------------------------------------
function MCQOptions({ questionId, options, value, onChange }: {
    questionId: string;
    options: { key: string; text: string }[];
    value: string;
    onChange: (val: string) => void;
}) {
    return (
        <div className="space-y-3">
            {options.map((opt) => {
                const selected = value === opt.key;
                return (
                    <label
                        key={opt.key}
                        className={cn(
                            "flex items-start gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all",
                            selected
                                ? "border-zinc-900 bg-zinc-900 text-white"
                                : "border-zinc-200 bg-white hover:border-zinc-400"
                        )}
                    >
                        <input
                            type="radio"
                            name={`mcq-${questionId}`}
                            value={opt.key}
                            checked={selected}
                            onChange={() => onChange(opt.key)}
                            className="sr-only"
                        />
                        <span className={cn(
                            "flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-sm",
                            selected ? "border-white text-white" : "border-zinc-400 text-zinc-600"
                        )}>
                            {opt.key}
                        </span>
                        <span className={cn("text-sm leading-relaxed mt-1", selected ? "text-white" : "text-zinc-700")}>
                            {opt.text}
                        </span>
                    </label>
                );
            })}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Photo upload / OCR tab
// ---------------------------------------------------------------------------
type OCRStatus = 'idle' | 'compressing' | 'uploading' | 'extracting' | 'done' | 'error';

function PhotoTab({ questionId, onConfirm }: { questionId: string; onConfirm: (text: string, imageUrl: string) => void }) {
    const fileRef = useRef<HTMLInputElement>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [compressedBlob, setCompressedBlob] = useState<Blob | null>(null);
    const [ocrStatus, setOcrStatus] = useState<OCRStatus>('idle');
    const [extractedText, setExtractedText] = useState('');
    const [imageUrl, setImageUrl] = useState('');
    const [error, setError] = useState('');

    const handleFile = useCallback(async (file: File) => {
        setError('');
        setOcrStatus('compressing');
        setPreview(null);
        setExtractedText('');
        try {
            const { blob, dataUrl } = await compressImage(file);
            setPreview(dataUrl);
            setCompressedBlob(blob);
            setOcrStatus('idle');
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Compression failed');
            setOcrStatus('error');
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith("image/")) handleFile(file);
    }, [handleFile]);

    const runOCR = async () => {
        if (!compressedBlob) return;
        setOcrStatus('uploading');
        setError('');
        try {
            const form = new FormData();
            form.append('file', compressedBlob, 'handwriting.jpg');
            form.append('question_id', questionId);

            const res = await fetch(`${API_URL}/ocr`, { method: 'POST', body: form });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: 'OCR failed' }));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            const data = await res.json();
            setImageUrl(data.image_url || '');
            setExtractedText(data.extracted_text || '');
            setOcrStatus('done');
        } catch (e) {
            setError(e instanceof Error ? e.message : 'OCR failed');
            setOcrStatus('error');
        }
    };

    const confirm = () => {
        onConfirm(extractedText, imageUrl);
    };

    const statusLabel: Record<OCRStatus, string> = {
        idle: '',
        compressing: 'Compressing image…',
        uploading: 'Uploading…',
        extracting: 'Extracting text…',
        done: 'Text extracted — review and confirm below.',
        error: 'Error occurred.',
    };

    return (
        <div className="space-y-4">
            {/* Drop zone */}
            <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-zinc-300 rounded-lg p-6 text-center cursor-pointer hover:border-zinc-400 transition-colors"
            >
                <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="sr-only"
                    onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                />
                {preview ? (
                    <img src={preview} alt="Answer preview" className="max-h-48 mx-auto rounded object-contain" />
                ) : (
                    <div className="flex flex-col items-center gap-2 text-zinc-400">
                        <Camera className="w-8 h-8" />
                        <p className="text-sm font-medium">Take a photo or upload image</p>
                        <p className="text-xs">JPEG, PNG, WEBP · will be compressed to &lt;1 MB</p>
                    </div>
                )}
            </div>

            {/* Status / error */}
            {ocrStatus === 'compressing' && (
                <div className="flex items-center gap-2 text-zinc-500 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" /> Compressing image…
                </div>
            )}
            {(ocrStatus === 'uploading' || ocrStatus === 'extracting') && (
                <div className="flex items-center gap-2 text-zinc-500 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" /> {statusLabel[ocrStatus]}
                </div>
            )}
            {error && (
                <div className="flex items-start gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
                </div>
            )}

            {/* Extract button */}
            {preview && ocrStatus !== 'done' && ocrStatus !== 'uploading' && ocrStatus !== 'extracting' && (
                <Button onClick={runOCR} disabled={!compressedBlob} className="w-full" variant="outline">
                    <ImageIcon className="w-4 h-4 mr-2" /> Extract Handwritten Text (OCR)
                </Button>
            )}

            {/* Extracted text — editable */}
            {ocrStatus === 'done' && (
                <div className="space-y-3">
                    <label className="block text-xs font-bold text-zinc-700 uppercase tracking-wider">
                        Extracted Text — review and edit if needed
                    </label>
                    <textarea
                        className="w-full min-h-[160px] p-4 border border-zinc-300 rounded-lg font-serif text-base leading-relaxed focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none resize-none"
                        value={extractedText}
                        onChange={(e) => setExtractedText(e.target.value)}
                        placeholder="OCR extracted text appears here — edit if needed…"
                    />
                    <Button onClick={confirm} className="w-full bg-zinc-900 hover:bg-zinc-800 text-white gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        Confirm — Use This as My Answer
                    </Button>
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main AnswerEditor
// ---------------------------------------------------------------------------
export function AnswerEditor() {
    const questions = useExamStore((s) => s.paper?.questions);
    const currentQuestionIndex = useExamStore((s) => s.currentQuestionIndex);
    const setAnswer = useExamStore((s) => s.setAnswer);
    const setAnswerImage = useExamStore((s) => s.setAnswerImage);
    const answers = useExamStore((s) => s.answers);
    const answerImages = useExamStore((s) => s.answerImages);
    const nextQuestion = useExamStore((s) => s.nextQuestion);
    const prevQuestion = useExamStore((s) => s.prevQuestion);
    const paper = useExamStore((s) => s.paper);

    const question = questions?.[currentQuestionIndex];
    const [activeTab, setActiveTab] = useState<'type' | 'photo'>('type');
    const [localValue, setLocalValue] = useState('');
    const [photoConfirmed, setPhotoConfirmed] = useState(false);
    const [warnShown, setWarnShown] = useState(false);

    // Sync textarea when question changes
    useEffect(() => {
        if (question) {
            setLocalValue(answers[question.id] || '');
            setPhotoConfirmed(!!answerImages[question.id]);
            // If already has image answer, default to photo tab
            if (answerImages[question.id]) setActiveTab('photo');
            else setActiveTab('type');
        }
    }, [question?.id]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        setLocalValue(val);
        if (question) setAnswer(question.id, val);
    };

    const handleMCQChange = (val: string) => {
        if (question) {
            setAnswer(question.id, val);
            setLocalValue(val);
        }
    };

    const handlePhotoConfirm = (text: string, url: string) => {
        if (!question) return;
        setAnswer(question.id, text);
        setAnswerImage(question.id, url);
        setPhotoConfirmed(true);
    };

    if (!question) {
        return <div className="p-8 text-center text-zinc-400">Loading question…</div>;
    }

    const isMCQ = question.type === 'mcq';

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto w-full p-6">
            {/* Question Display */}
            <div className="mb-6 p-6 bg-white border border-zinc-200 rounded-lg shadow-sm">
                <div className="flex justify-between items-start mb-4 border-b border-zinc-100 pb-4">
                    <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest">
                        Question {question.questionNumber}
                        {question.topic && (
                            <span className="ml-2 font-normal text-zinc-400 normal-case tracking-normal">— {question.topic}</span>
                        )}
                    </h2>
                    <div className="flex items-center gap-2">
                        {isMCQ && (
                            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">MCQ</span>
                        )}
                        <span className="bg-zinc-100 text-zinc-600 px-2 py-1 rounded text-xs font-medium">
                            {question.marks} {question.marks === 1 ? 'Mark' : 'Marks'}
                        </span>
                    </div>
                </div>

                {/* Inline question image */}
                {question.has_image && question.imageUrl && (
                    <div className="mb-4 rounded-md overflow-hidden border border-zinc-200">
                        <img
                            src={question.imageUrl}
                            alt={`Diagram for Question ${question.questionNumber}`}
                            className="max-w-full object-contain max-h-72 mx-auto block"
                        />
                        <p className="text-center text-xs text-zinc-400 py-1 bg-zinc-50 border-t border-zinc-100">
                            Figure — Question {question.questionNumber}
                        </p>
                    </div>
                )}

                <div
                    className="prose prose-zinc max-w-none prose-p:leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: question.text }}
                />
            </div>

            {/* Answer area */}
            {isMCQ ? (
                <div className="bg-white border border-zinc-200 rounded-lg p-6 shadow-sm">
                    <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-4">Select one answer</p>
                    <MCQOptions
                        questionId={question.id}
                        options={question.mcqOptions || []}
                        value={localValue}
                        onChange={handleMCQChange}
                    />
                </div>
            ) : (
                <div className="flex-1 flex flex-col bg-white border border-zinc-200 rounded-lg shadow-sm overflow-hidden">
                    {/* Tabs */}
                    <div className="flex border-b border-zinc-200">
                        <button
                            onClick={() => setActiveTab('type')}
                            className={cn(
                                "flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors",
                                activeTab === 'type'
                                    ? "border-b-2 border-zinc-900 text-zinc-900"
                                    : "text-zinc-400 hover:text-zinc-600"
                            )}
                        >
                            <Keyboard className="w-4 h-4" /> Type Answer
                        </button>
                        <button
                            onClick={() => setActiveTab('photo')}
                            className={cn(
                                "flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors",
                                activeTab === 'photo'
                                    ? "border-b-2 border-zinc-900 text-zinc-900"
                                    : "text-zinc-400 hover:text-zinc-600"
                            )}
                        >
                            <Camera className="w-4 h-4" /> Upload Photo
                            {answerImages[question.id] && (
                                <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                            )}
                        </button>
                    </div>

                    <div className="flex-1 p-5">
                        {activeTab === 'type' ? (
                            <div className="flex flex-col h-full gap-2">
                                <textarea
                                    className="flex-1 min-h-[340px] w-full resize-none p-4 rounded-md border border-zinc-200 focus:border-zinc-900 focus:ring-1 focus:ring-zinc-900 outline-none font-serif text-lg leading-relaxed bg-white text-zinc-800"
                                    placeholder="Start writing your answer here…"
                                    value={localValue}
                                    onChange={handleTextChange}
                                    spellCheck={false}
                                />
                                <div className="flex justify-between items-center text-xs text-zinc-400">
                                    <span>
                                        {answers[question.id] ? (
                                            <span className="text-green-600 flex items-center gap-1">
                                                <CheckCircle2 className="w-3 h-3 inline" /> Auto-saved
                                            </span>
                                        ) : 'Not yet answered'}
                                    </span>
                                    <span>
                                        {localValue.split(/\s+/).filter(Boolean).length} words
                                    </span>
                                    {localValue.length > 0 && localValue.length < 20 && (
                                        <span className="text-amber-500 text-xs">Min. 20 characters required</span>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div>
                                {photoConfirmed && answerImages[question.id] ? (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg p-3 text-sm font-medium">
                                            <CheckCircle2 className="w-4 h-4" />
                                            Handwritten answer confirmed.
                                        </div>
                                        {answerImages[question.id] && (
                                            <div className="border border-zinc-200 rounded-lg overflow-hidden">
                                                <img
                                                    src={answerImages[question.id]}
                                                    alt="Your handwritten answer"
                                                    className="max-w-full max-h-48 object-contain mx-auto block"
                                                />
                                            </div>
                                        )}
                                        <div className="bg-zinc-50 border border-zinc-200 rounded-lg p-4">
                                            <p className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Extracted text (your answer)</p>
                                            <p className="text-sm text-zinc-700 font-serif leading-relaxed">{answers[question.id]}</p>
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => { setPhotoConfirmed(false); setAnswerImage(question.id, ''); }}
                                        >
                                            Re-upload Photo
                                        </Button>
                                    </div>
                                ) : (
                                    <PhotoTab
                                        questionId={question.id}
                                        onConfirm={handlePhotoConfirm}
                                    />
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Navigation */}
            <div className="flex flex-col gap-2 mt-4">
                {warnShown && (
                    <div className="w-full text-center text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
                        Answer is very short — are you sure? Continuing in a moment…
                    </div>
                )}
                <div className="flex justify-between items-center">
                    <Button
                        variant="outline"
                        onClick={prevQuestion}
                        disabled={currentQuestionIndex === 0}
                        className="gap-1"
                    >
                        <ChevronLeft className="w-4 h-4" /> Previous
                    </Button>
                    <span className="text-sm text-zinc-400">
                        {currentQuestionIndex + 1} / {questions?.length}
                    </span>
                    <Button
                        variant="outline"
                        onClick={() => {
                            if (!isMCQ && localValue.length > 0 && localValue.length < 20 && !warnShown) {
                                setWarnShown(true);
                                setTimeout(() => {
                                    setWarnShown(false);
                                    nextQuestion();
                                }, 3000);
                            } else {
                                nextQuestion();
                            }
                        }}
                        disabled={currentQuestionIndex === (questions?.length || 0) - 1}
                        className="gap-1"
                    >
                        Next <ChevronRight className="w-4 h-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
