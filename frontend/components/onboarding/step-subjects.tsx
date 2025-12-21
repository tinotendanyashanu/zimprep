"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Search, Plus } from "lucide-react";
import { useState } from "react";
import { SUBJECTS_DB } from "@/lib/data";

interface StepSubjectsProps {
  selected: string[];
  onChange: (subjects: string[]) => void;
}

export function StepSubjects({ selected, onChange }: StepSubjectsProps) {
  const [search, setSearch] = useState("");

  const toggleSubject = (subject: string) => {
    if (selected.includes(subject)) {
      onChange(selected.filter((s) => s !== subject));
    } else {
      onChange([...selected, subject]);
    }
  };

  const filteredSubjects = SUBJECTS_DB.filter(s => 
    s.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">
      <div className="text-center">
        <h2 className="text-calm-h2 mb-2">Which subjects are you studying?</h2>
        <p className="text-calm-body text-base">Select all the subjects you plan to sit for.</p>
      </div>

      <div className="max-w-2xl mx-auto space-y-4">
        {/* Search */}
        <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
                placeholder="Search subjects..." 
                className="pl-10 h-12 rounded-xl bg-zinc-50 border-zinc-200"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
            />
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-[400px] overflow-y-auto p-1">
            {filteredSubjects.map((subject) => {
                const isSelected = selected.includes(subject);
                return (
                    <button
                        key={subject}
                        onClick={() => toggleSubject(subject)}
                        className={cn(
                            "flex items-center justify-start text-left p-4 rounded-xl text-sm font-medium transition-all duration-200 border",
                            isSelected 
                                ? "bg-primary text-primary-foreground border-primary shadow-md" 
                                : "bg-white text-zinc-600 border-zinc-200 hover:border-primary/30 hover:bg-zinc-50"
                        )}
                    >
                       <span className="truncate">{subject}</span>
                    </button>
                )
            })}
        </div>
        
        {selected.length === 0 && (
            <p className="text-center text-sm text-red-500 font-medium">Please select at least one subject.</p>
        )}
        {selected.length > 5 && (
            <p className="text-center text-xs text-amber-600">Tip: Focusing on too many subjects can be overwhelming.</p>
        )}
      </div>
    </div>
  );
}
