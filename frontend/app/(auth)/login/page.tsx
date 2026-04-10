"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { data: authData, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    const user = authData.user;
    if (user) {
      let destination = "/dashboard";

      const { data: employee } = await supabase
        .from("employee")
        .select("role")
        .eq("user_id", user.id)
        .maybeSingle();

      if (employee) {
        destination = employee.role === "admin" ? "/admin" : "/workstation";
      } else {
        const { data: parent } = await supabase
          .from("parent")
          .select("id")
          .eq("id", user.id)
          .maybeSingle();
        if (parent) destination = "/parent/dashboard";
      }

      router.push(destination);
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <div className="bg-card border border-border rounded-2xl p-8 shadow-sm">
      {/* Logo / Brand */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 mb-6">
          <span className="text-2xl font-bold text-foreground">ZimPrep</span>
        </div>
        <h1 className="text-2xl font-semibold text-foreground">Welcome back</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Sign in to continue your exam prep
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            Email
          </label>
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
          <label
            htmlFor="password"
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring transition"
          />
        </div>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-primary text-primary-foreground font-medium text-sm rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="mt-6 space-y-2 text-center text-sm text-muted-foreground">
        <p>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary font-medium hover:underline">
            Register as Student
          </Link>
        </p>
        <p>
          Are you a parent?{" "}
          <Link href="/register-parent" className="text-primary font-medium hover:underline">
            Register as Parent
          </Link>
        </p>
      </div>
    </div>
  );
}
