import { Recommendation } from "./types";
import { getUser } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getRecommendations(): Promise<Recommendation[]> {
  const user = getUser();
  if (!user) return [];

  const res = await fetch(`${API_URL}/students/${user.id}/recommendations`);
  if (!res.ok) return [];
  return res.json();
}

// Empty fallback — no more fake data
export const MOCK_RECOMMENDATIONS: Recommendation[] = [];
