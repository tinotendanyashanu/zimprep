"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

type ExamBoard = "zimsec" | "cambridge";

const ZIMSEC_LEVELS = [
  { value: "Grade7", label: "Grade 7" },
  { value: "O", label: "O Level (Form 4)" },
  { value: "A", label: "A Level (Form 6)" },
] as const;

const CAMBRIDGE_LEVELS = [
  { value: "IGCSE", label: "Cambridge IGCSE" },
  { value: "AS_Level", label: "Cambridge AS Level" },
  { value: "A_Level", label: "Cambridge A Level" },
] as const;

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [examBoard, setExamBoard] = useState<ExamBoard | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [level, setLevel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const levels = examBoard === "cambridge" ? CAMBRIDGE_LEVELS : ZIMSEC_LEVELS;

  function handleSelectBoard(board: ExamBoard) {
    setExamBoard(board);
    setLevel("");
    setStep(2);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!examBoard || !level) return;
    setError(null);
    setLoading(true);

    const supabase = createClient();

    const { data, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (signUpError) {
      setError(signUpError.message);
      setLoading(false);
      return;
    }

    const userId = data.user?.id;
    if (!userId) {
      setError("Sign up failed — please try again.");
      setLoading(false);
      return;
    }

    const { error: profileError } = await supabase.from("student").insert({
      id: userId,
      email,
      name,
      level,
      exam_board: examBoard,
      subscription_tier: "starter",
    });

    if (profileError) {
      setError(profileError.message);
      setLoading(false);
      return;
    }

    // Assign student role via server-side API (uses service key, bypasses RLS)
    const session = data.session;
    if (session) {
      await fetch("/api/auth/assign-role", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ role: "student" }),
      });
    }

    router.push("/dashboard");
    router.refresh();
  }

  // ── Step 1: Choose exam board ────────────────────────────────────────────────
  if (step === 1) {
    return (
      <div className="bg-card border border-border rounded-2xl p-8 shadow-sm">
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 mb-6">
            <span className="text-2xl font-bold text-foreground">ZimPrep</span>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Create your account</h1>
          <p className="text-muted-foreground text-sm mt-1">First, which exam board are you studying?</p>
        </div>

        <div className="space-y-4">
          <button
            onClick={() => handleSelectBoard("zimsec")}
            className="w-full p-5 rounded-xl border-2 border-border hover:border-primary hover:bg-primary/5 transition-all text-left group"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-foreground text-base group-hover:text-primary transition-colors">ZIMSEC</p>
                <p className="text-sm text-muted-foreground mt-0.5">Zimbabwe School Examinations Council</p>
                <div className="flex gap-2 mt-3 flex-wrap">
                  {["Grade 7", "O Level", "A Level"].map((l) => (
                    <span key={l} className="text-xs px-2 py-0.5 bg-zinc-100 rounded-full text-zinc-600">{l}</span>
                  ))}
                </div>
              </div>
              <span className="text-2xl">🇿🇼</span>
            </div>
          </button>

          <button
            onClick={() => handleSelectBoard("cambridge")}
            className="w-full p-5 rounded-xl border-2 border-border hover:border-primary hover:bg-primary/5 transition-all text-left group"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-foreground text-base group-hover:text-primary transition-colors">Cambridge</p>
                <p className="text-sm text-muted-foreground mt-0.5">Cambridge Assessment International Education</p>
                <div className="flex gap-2 mt-3 flex-wrap">
                  {["IGCSE", "AS Level", "A Level"].map((l) => (
                    <span key={l} className="text-xs px-2 py-0.5 bg-zinc-100 rounded-full text-zinc-600">{l}</span>
                  ))}
                </div>
              </div>
              <span className="text-2xl">🎓</span>
            </div>
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    );
  }

  // ── Step 2: Details + level ──────────────────────────────────────────────────
  return (
    <div className="bg-card border border-border rounded-2xl p-8 shadow-sm">
      <div className="mb-6">
        <button
          onClick={() => setStep(1)}
          className="text-sm text-muted-foreground hover:text-foreground mb-4 flex items-center gap-1 transition-colors"
        >
          ← Back
        </button>
        <div className="inline-flex items-center gap-2 mb-1">
          <span className="text-2xl font-bold text-foreground">ZimPrep</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${examBoard === "cambridge" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>
            {examBoard === "cambridge" ? "Cambridge" : "ZIMSEC"}
          </span>
        </div>
        <h1 className="text-2xl font-semibold text-foreground">Your details</h1>
        <p className="text-muted-foreground text-sm mt-1">Almost there — fill in your info.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1.5">Full name</label>
          <input
            id="name"
            type="text"
            autoComplete="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tendai Moyo"
            className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring transition"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring transition"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1.5">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring transition"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">Exam level</label>
          <div className="grid grid-cols-1 gap-2">
            {levels.map((l) => (
              <button
                key={l.value}
                type="button"
                onClick={() => setLevel(l.value)}
                className={`py-2.5 px-4 rounded-lg text-sm font-medium border transition text-left ${
                  level === l.value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background text-foreground border-border hover:border-primary/50"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading || !level}
          className="w-full py-2.5 px-4 bg-primary text-primary-foreground font-medium text-sm rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-primary font-medium hover:underline">Sign in</Link>
      </p>
    </div>
  );
}
