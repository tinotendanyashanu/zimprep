"use client";

import { DashboardHeader } from "@/components/dashboard/header";
import { getPapersForSubject } from "@/lib/data";
import { ArrowLeft, Book, Clock, PlayCircle } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function PaperPage() {
    const params = useParams();
    const router = useRouter();
    const subject = decodeURIComponent(params.subject as string);
    const paperId = params.paper as string;
    
    const papers = getPapersForSubject(subject);
    const paper = papers.find(p => p.id === paperId);

    if (!paper) {
        return <div className="p-12">Paper not found.</div>;
    }

    const startPractice = (mode: string) => {
        if (mode === 'exam') {
            router.push(`/subjects/${encodeURIComponent(subject)}/papers/${paperId}/start`);
        } else {
            alert("Practice Mode coming soon!");
        }
    };

    return (
        <div className="min-h-screen bg-zinc-50/50">
            <DashboardHeader title={paper.name} />

            <main className="max-w-4xl mx-auto p-6 md:p-12 space-y-8 animate-in fade-in duration-500">
                <Link href={`/subjects/${encodeURIComponent(subject)}`} className="text-sm font-medium text-muted-foreground hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="w-4 h-4" /> Back to {subject}
                </Link>

                <div className="grid md:grid-cols-3 gap-8">
                    {/* Left: Paper Info */}
                    <div className="md:col-span-2 space-y-8">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight mb-2">{paper.name}</h1>
                             <div className="flex items-center gap-4 text-sm text-zinc-500">
                                <span className="flex items-center gap-1.5 bg-zinc-100 px-2 py-1 rounded">
                                    <Clock className="w-3.5 h-3.5" /> {paper.duration}
                                </span>
                                <span className="flex items-center gap-1.5 bg-zinc-100 px-2 py-1 rounded">
                                    <Book className="w-3.5 h-3.5" /> {paper.type}
                                </span>
                             </div>
                        </div>

                        <div className="prose prose-zinc">
                            <h3 className="text-lg font-bold">About this Paper</h3>
                            <p>{paper.description}</p>
                            <p>
                                This mock exam is designed to replicate the actual ZIMSEC experience. 
                                Ensure you have a stable internet connection before starting the timed mode.
                            </p>
                        </div>
                    </div>

                    {/* Right: Mode Selection */}
                    <div className="md:col-span-1 space-y-4">
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Select Mode</h3>
                        
                        <Card className="p-4 hover:border-primary cursor-pointer transition-all border-l-4 border-l-primary" onClick={() => startPractice('exam')}>
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-lg">Exam Mode</span>
                                <PlayCircle className="w-5 h-5 text-primary" />
                            </div>
                            <p className="text-xs text-muted-foreground mb-3">Timed. No hints. Full simulation.</p>
                            <Button className="w-full h-8 text-xs font-bold">Start Exam</Button>
                        </Card>

                        <Card className="p-4 hover:border-primary/50 cursor-pointer transition-all border-l-4 border-l-blue-500" onClick={() => startPractice('practice')}>
                            <div className="flex justify-between items-start mb-2">
                                <span className="font-bold text-lg">Practice Mode</span>
                                <Book className="w-5 h-5 text-blue-500" />
                            </div>
                            <p className="text-xs text-muted-foreground mb-3">Untimed. Instant feedback.</p>
                            <Button variant="outline" className="w-full h-8 text-xs">Start Practice</Button>
                        </Card>
                    </div>
                </div>
            </main>
        </div>
    );
}
