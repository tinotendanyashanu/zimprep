import { Recommendation } from "@/lib/recommendations/types";
import { RecommendationCard } from "./recommendation-card";

interface RecommendationListProps {
  items: Recommendation[];
}

export function RecommendationList({ items }: RecommendationListProps) {
  if (!items || items.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
        <p className="text-lg font-medium">Insufficient performance data</p>
        <p className="mt-2 text-sm max-w-sm">
          Complete more practice papers or topic exercises to generate evidence-based recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <RecommendationCard key={item.id} recommendation={item} />
      ))}
    </div>
  );
}
