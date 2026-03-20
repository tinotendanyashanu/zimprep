/**
 * Catalog data — subjects and papers fetched from the backend.
 * SUBJECTS_DB is a static fallback for UI when the API hasn't been called yet.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Static list kept as a fallback / for instant subject-selector rendering.
// Backend is the source of truth; these names must match subject.name in the DB.
export const SUBJECTS_DB = [
  "Mathematics", "English Language", "Shona", "Ndebele",
  "Physics", "Chemistry", "Biology", "Combined Science",
  "History", "Geography", "Commerce", "Principles of Accounts",
  "Computer Science", "Literature in English", "Agriculture",
  "Business Studies", "Economics", "Sociology", "Divinity",
];

export interface Subject {
  id: string;
  name: string;
  level: 'Grade7' | 'O' | 'A';
}

export interface PaperMeta {
  id: string;
  year: number;
  paper_number: number;
  status: string;
}

export interface Paper {
  id: string;
  name: string;
  type: 'Multiple Choice' | 'Structured' | 'Practical' | 'Essay';
  duration: string;
  description: string;
}

/** Fetch all subjects from the backend catalog. */
export async function getSubjects(level?: string): Promise<Subject[]> {
  const url = new URL(`${API_URL}/catalog/subjects`);
  if (level) url.searchParams.set('level', level);
  const res = await fetch(url.toString());
  if (!res.ok) return [];
  return res.json();
}

/** Fetch the subject record by name. */
export async function getSubjectByName(name: string): Promise<Subject | null> {
  const url = new URL(`${API_URL}/catalog/subjects`);
  url.searchParams.set('name', name);
  const res = await fetch(url.toString());
  if (!res.ok) return null;
  const list: Subject[] = await res.json();
  return list[0] ?? null;
}

/** Fetch papers available for a subject. */
export async function getPapersForSubjectId(subjectId: string): Promise<PaperMeta[]> {
  const res = await fetch(`${API_URL}/catalog/subjects/${subjectId}/papers`);
  if (!res.ok) return [];
  return res.json();
}

/** Look up a specific paper UUID. */
export async function findPaperId(
  subjectId: string,
  year: number,
  paperNumber: number,
): Promise<string | null> {
  const url = new URL(`${API_URL}/catalog/papers`);
  url.searchParams.set('subject_id', subjectId);
  url.searchParams.set('year', String(year));
  url.searchParams.set('paper_number', String(paperNumber));
  const res = await fetch(url.toString());
  if (!res.ok) return null;
  const data = await res.json();
  return data.id ?? null;
}

// Legacy export kept so old imports don't break (returns empty array now)
export const MOCK_PAPERS: Record<string, Paper[]> = {};
export function getPapersForSubject(_subject: string): Paper[] { return []; }
