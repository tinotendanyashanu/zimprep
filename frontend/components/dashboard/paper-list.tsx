"use client";

import { Card } from "@/components/ui/card";
import { Paper } from "@/lib/data";
import { Badge } from "@/components/ui/badge";
import { Clock, ArrowRight, FileText } from "lucide-react";
import { useRouter } from "next/navigation";

interface PaperListProps {
  subject: string;
  papers: Paper[];
}

export function PaperList({ subject, papers }: PaperListProps) {
    const router = useRouter();

    const handleSelectPaper = (paperId: string) => {
        router.push(`/subjects/${encodeURIComponent(subject)}/papers/${paperId}`);
    };

    return (
        <div className="grid gap-4">
            {papers.map((paper) => (
                <Card 
                    key={paper.id} 
                    className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-primary/50 transition-all cursor-pointer group"
                    onClick={() => handleSelectPaper(paper.id)}
                >
                    <div className="flex items-start gap-4">
                        <div className="p-3 bg-zinc-50 rounded-xl group-hover:bg-primary/5 transition-colors hidden md:block">
                            <FileText className="w-6 h-6 text-zinc-400 group-hover:text-primary/80" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-bold text-lg">{paper.name}</h4>
                                <Badge variant="secondary" className="font-normal text-xs">{paper.type}</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground max-w-md">{paper.description}</p>
                            <div className="flex items-center gap-1.5 text-xs text-zinc-500 mt-2 md:hidden">
                                <Clock className="w-3.5 h-3.5" />
                                {paper.duration}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                         <div className="hidden md:flex items-center gap-1.5 text-sm font-medium text-zinc-500 bg-zinc-50 px-3 py-1.5 rounded-lg">
                            <Clock className="w-4 h-4" />
                            {paper.duration}
                        </div>
                        <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-400 group-hover:bg-primary group-hover:text-white transition-all ml-auto md:ml-0">
                            <ArrowRight className="w-4 h-4" />
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    );
}
