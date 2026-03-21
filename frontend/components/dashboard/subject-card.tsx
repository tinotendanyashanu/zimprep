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
        className="p-6 rounded-[2rem] border-4 border-border shadow-gamified hover:shadow-gamified-lg hover:border-primary/30 transition-all cursor-pointer group bg-card hover:-translate-y-1 active:translate-y-0 active:shadow-sm relative overflow-hidden flex flex-col justify-between"
        onClick={() => router.push(`/subjects/${encodeURIComponent(subject)}`)}
    >
      <div className="flex justify-between items-start mb-6">
          <div className="p-4 bg-secondary rounded-2xl group-hover:scale-110 group-hover:bg-primary/20 transition-all shadow-sm border-2 border-border/50">
             <BookOpen className="w-7 h-7 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          <span className="text-xs font-black px-3 py-1.5 bg-accent/10 border-2 border-accent/20 rounded-xl text-accent uppercase tracking-wider">
            {paperCount} Papers
          </span>
      </div>
      
      <div className="mb-6">
        <h4 className="text-2xl font-black text-foreground mb-2 group-hover:text-primary transition-colors tracking-tight">{subject}</h4>
        <div className="flex items-center gap-2 text-sm font-bold text-muted-foreground">
            <Clock className="w-4 h-4 text-orange-400" />
            <span>0 hrs studied</span>
        </div>
      </div>

      <div className="space-y-3">
         <div className="flex justify-between font-bold text-xs text-muted-foreground uppercase tracking-wider">
            <span>Progress</span>
            <span className="text-foreground">{progress}%</span>
         </div>
         <div className="h-4 w-full bg-secondary border-2 border-border/50 rounded-full overflow-hidden shadow-inner p-0.5">
            <div className="h-full bg-primary rounded-full transition-all duration-1000" style={{ width: `${progress}%` }} />
         </div>
      </div>

      <div className="mt-8 flex justify-end">
          <Button variant="secondary" size="sm" className="w-full text-foreground gap-1 border-border/50 font-bold group-hover:bg-primary group-hover:text-white group-hover:border-primary shadow-sm h-12">
             Continue <ChevronRight className="w-5 h-5" />
          </Button>
      </div>
    </Card>
  );
}
