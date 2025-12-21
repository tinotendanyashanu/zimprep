import { getRecommendations } from "@/lib/recommendations/mock-data";
import { RecommendationList } from "@/components/recommendations/recommendation-list";

export default async function RecommendationsPage() {
  const recommendations = await getRecommendations();

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-light tracking-tight text-foreground">
          Recommendations
        </h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Analysis based on your recent performance history. These suggestions point to areas where data shows opportunities for improvement.
        </p>
      </div>

      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-600/90 dark:text-amber-500/90">
        <span className="font-semibold">Note:</span> These are evidence-based suggestions, not predictions of your final grade. You are free to prioritize other topics as needed.
      </div>

      <RecommendationList items={recommendations} />
    </div>
  );
}
