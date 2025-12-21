"use client";

import { DashboardHeader } from "@/components/dashboard/header";
import { PaperList } from "@/components/dashboard/paper-list";
import { getPapersForSubject } from "@/lib/data";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function SubjectPage() {
    const params = useParams();
    const subject = decodeURIComponent(params.subject as string);
    const papers = getPapersForSubject(subject);

    return (
        <div className="min-h-screen bg-zinc-50/50">
            <DashboardHeader title="Subject Overview" />

            <main className="max-w-4xl mx-auto p-6 md:p-12 space-y-8 animate-in fade-in duration-500">
                <div className="mb-4">
                    <Link href="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-primary flex items-center gap-1 mb-6">
                        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
                    </Link>
                    <h1 className="text-4xl font-bold tracking-tight mb-2">{subject}</h1>
                    <p className="text-muted-foreground text-lg">
                        Select a paper to begin practicing.
                    </p>
                </div>

                <div className="grid gap-8">
                     <section>
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Availability</h3>
                        <div className="bg-red-50 border border-red-100 p-4 rounded-xl text-red-900 text-sm mb-6">
                           <strong>Important:</strong> This is a mock environment. Progress is simulated.
                        </div>
                        
                        <PaperList subject={subject} papers={papers} />
                     </section>
                </div>
            </main>
        </div>
    );
}
