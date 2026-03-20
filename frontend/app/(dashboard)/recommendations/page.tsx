"use client";

import { useEffect, useState } from "react";
import { RecommendationList } from "@/components/recommendations/recommendation-list";
import { Recommendation } from "@/lib/recommendations/types";
import { getRecommendations } from "@/lib/recommendations/mock-data";
import { Loader2 } from "lucide-react";

export default function RecommendationsPage() {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecommendations().then((data) => {
      setItems(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-light tracking-tight text-foreground">Recommendations</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Analysis based on your recent performance history. These suggestions point to areas where data shows opportunities for improvement.
        </p>
      </div>

      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-600/90">
        <span className="font-semibold">Note:</span> These are evidence-based suggestions, not predictions of your final grade.
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-zinc-500 text-center py-12">
          No recommendations yet — complete some practice questions to get personalised suggestions.
        </p>
      ) : (
        <RecommendationList items={items} />
      )}
    </div>
  );
}
