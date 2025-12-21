"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, ChevronRight, Clock } from "lucide-react";
import { useRouter } from "next/navigation";
import { getPapersForSubject } from "@/lib/data";

interface SubjectCardProps {
  subject: string;
}

export function SubjectCard({ subject }: SubjectCardProps) {
  const router = useRouter();
  const papers = getPapersForSubject(subject);
  const paperCount = papers.length;

  // Mock progress - random integer between 0 and 30 for realism
  const progress = Math.floor(Math.random() * 30); 

  return (
    <Card 
        className="p-6 rounded-3xl border-border hover:border-primary/50 transition-all cursor-pointer group bg-white relative overflow-hidden"
        onClick={() => router.push(`/subjects/${encodeURIComponent(subject)}`)}
    >
      <div className="flex justify-between items-start mb-6">
          <div className="p-3 bg-zinc-100 rounded-xl group-hover:bg-primary/10 transition-colors">
             <BookOpen className="w-6 h-6 text-zinc-500 group-hover:text-primary" />
          </div>
          <span className="text-xs font-medium px-2.5 py-1 bg-zinc-100 rounded-full text-zinc-600">
            {paperCount} Papers
          </span>
      </div>
      
      <div className="mb-4">
        <h4 className="text-xl font-bold mb-1 group-hover:text-primary transition-colors">{subject}</h4>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span>0 hrs studied</span>
        </div>
      </div>

      <div className="space-y-2">
         <div className="flex justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{progress}%</span>
         </div>
         <div className="h-1.5 w-full bg-zinc-100 rounded-full overflow-hidden">
            <div className="h-full bg-primary/80 rounded-full" style={{ width: `${progress}%` }} />
         </div>
      </div>

      <div className="mt-6 pt-4 border-t border-zinc-100 flex justify-end">
          <Button variant="ghost" size="sm" className="text-primary hover:text-primary hover:bg-primary/5 gap-1 p-0 h-auto font-medium">
             Continue <ChevronRight className="w-4 h-4" />
          </Button>
      </div>
    </Card>
  );
}
