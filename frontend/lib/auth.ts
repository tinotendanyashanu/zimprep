/**
 * Authentication — backed by Supabase Auth.
 *
 * getUser() is synchronous (reads localStorage cache) so existing callers
 * don't need to be made async. The cache is written on login/register and
 * cleared on logout. For server-authoritative checks use getSessionUser().
 */
import { supabase } from './supabase';

export interface User {
  id: string;
  email: string;
  role: string;
  name?: string;
}

const CACHE_KEY = 'zimprep_user';

// ---------------------------------------------------------------------------
// Cache helpers (synchronous)
// ---------------------------------------------------------------------------

function writeCache(user: User): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CACHE_KEY, JSON.stringify(user));
  // Legacy key kept for backward compat with onboarding page
  localStorage.setItem('isAuthenticated', 'true');
}

function clearCache(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(CACHE_KEY);
  localStorage.removeItem('isAuthenticated');
  localStorage.removeItem('zimprep_token');
}

/** Synchronous — reads from localStorage cache. Returns null if not logged in. */
export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(CACHE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

/** Async — checks live Supabase session. Use for auth guards. */
export async function getSessionUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) { clearCache(); return null; }
  const u: User = {
    id: user.id,
    email: user.email!,
    role: (user.user_metadata?.role as string) || 'student',
    name: user.user_metadata?.name as string | undefined,
  };
  writeCache(u);
  return u;
}

export function isAuthenticated(): boolean {
  return !!getUser();
}

// ---------------------------------------------------------------------------
// Auth actions
// ---------------------------------------------------------------------------

export async function register(
  email: string,
  password: string,
  name: string,
): Promise<User> {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { name, role: 'student' } },
  });
  if (error) throw new Error(error.message);
  const u: User = {
    id: data.user!.id,
    email: data.user!.email!,
    role: 'student',
    name,
  };
  writeCache(u);
  return u;
}

export async function login(email: string, password: string): Promise<User> {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw new Error(error.message);
  const u: User = {
    id: data.user.id,
    email: data.user.email!,
    role: (data.user.user_metadata?.role as string) || 'student',
    name: data.user.user_metadata?.name as string | undefined,
  };
  writeCache(u);
  return u;
}

export async function logout(): Promise<void> {
  await supabase.auth.signOut();
  clearCache();
}

// Legacy stubs — kept so existing imports don't break
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  expires_in: number;
}
export function setAuthToken(_token: string): void {}
export function getAuthToken(): string | null { return null; }
export function clearAuth(): void { clearCache(); }
export function setUser(user: User): void { writeCache(user); }
