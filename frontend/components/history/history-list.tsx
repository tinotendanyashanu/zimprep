"use client";

import { AttemptHistoryItem } from "@/lib/history/types";
import { HistoryRow } from "./history-row";

interface HistoryListProps {
  attempts: AttemptHistoryItem[];
}

import { EmptyState } from "@/components/system/EmptyState";
import { FileClock } from "lucide-react";
import { useRouter } from "next/navigation";

export function HistoryList({ attempts }: HistoryListProps) {
  const router = useRouter();

  if (attempts.length === 0) {
    return (
      <EmptyState
        icon={FileClock}
        title="No practice history yet"
        description="Complete a paper to see your progress tracked here."
        action={{
          label: "Start Practice",
          onClick: () => router.push('/dashboard')
        }}
        className="mt-8"
      />
    );
  }

  return (
    <div className="space-y-1">
      {attempts.map((attempt) => (
        <HistoryRow key={attempt.attempt_id} attempt={attempt} />
      ))}
    </div>
  );
}
