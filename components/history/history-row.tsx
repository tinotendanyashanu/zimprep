"use client";

import { AttemptHistoryItem } from "@/lib/history/types";
import { Button } from "@/components/ui/button";
import { ChevronRight, RefreshCw, FileText } from "lucide-react";
import Link from "next/link";

interface HistoryRowProps {
  attempt: AttemptHistoryItem;
}

export function HistoryRow({ attempt }: HistoryRowProps) {
  // Format date: "15 May 2024"
  const formattedDate = new Date(attempt.date).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="group flex items-center justify-between p-4 bg-white border border-border rounded-xl hover:border-gray-300 transition-all mb-3">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400 group-hover:text-gray-600 transition-colors">
          <FileText className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{attempt.subject}</h4>
          <p className="text-sm text-gray-500">
            {attempt.paper} • {formattedDate}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-sm font-medium text-gray-900">
            {attempt.score} / {attempt.total}
          </div>
          <div className="text-xs text-gray-500">Score</div>
        </div>

        <div className="flex items-center gap-2">
            {/* Mocked action for now, would link to actual play route */}
           <Button variant="ghost" size="sm" className="h-8 px-2 text-gray-500 hover:text-gray-900">
              <RefreshCw className="w-4 h-4 mr-1" />
              <span className="text-xs">Retry</span>
           </Button>
           
           <Link href={`/results/${attempt.attempt_id}`}>
             <Button variant="outline" size="sm" className="h-8 text-xs font-normal border-gray-200">
                View
                <ChevronRight className="w-3 h-3 ml-1" />
             </Button>
           </Link>
        </div>
      </div>
    </div>
  );
}
