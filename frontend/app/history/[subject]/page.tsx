import { SubjectProgressSummary } from "@/components/history/subject-progress-summary";
import { ProgressChart } from "@/components/history/progress-chart";
import { getSubjectProgress } from "@/lib/history/data";
import { Button } from "@/components/ui/button";
import { ArrowLeft, BookOpen, AlertCircle } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ subject: string }>;
}

export default async function SubjectHistoryPage({ params }: PageProps) {
  // Await the params object before accessing properties
  const { subject } = await params;
  
  if (!subject) {
      notFound();
  }

  const decodedSubject = decodeURIComponent(subject);
  const progress = await getSubjectProgress('', decodedSubject);

  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
            <Link href="/history">
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <ArrowLeft className="w-4 h-4" />
                </Button>
            </Link>
            <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{decodedSubject}</h1>
                <p className="text-gray-500">Progress Report • {progress.level}</p>
            </div>
        </div>

        {/* Summary Stats */}
        <SubjectProgressSummary progress={progress} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Chart Column */}
            <div className="lg:col-span-2 space-y-8">
                <ProgressChart data={progress.trend} />
                
                {/* Suggested Focus */}
                <div className="bg-white p-6 rounded-xl border border-border">
                     <h3 className="text-lg font-bold text-zinc-900 mb-4 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-zinc-500" />
                        Suggested Focus
                     </h3>
                     <div className="space-y-3">
                        {progress.suggested_focus.map((topic, i) => (
                            <div key={i} className="p-3 bg-zinc-50 rounded-lg text-sm text-zinc-700 border border-zinc-100">
                                {topic}
                            </div>
                        ))}
                     </div>
                </div>
            </div>

            {/* Sidebar Column */}
            <div className="space-y-6">
                <div className="bg-white p-6 rounded-xl border border-border">
                    <h3 className="text-lg font-bold text-zinc-900 mb-4 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-zinc-500" />
                        Common Weak Topics
                    </h3>
                    <p className="text-sm text-zinc-500 mb-4">
                        Based on your recent incorrect answers.
                    </p>
                    <ul className="space-y-2">
                        {progress.weak_topics.map((topic, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-zinc-700">
                                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-red-400 flex-shrink-0" />
                                <span>{topic}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
