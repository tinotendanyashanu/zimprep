"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { register } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const form = e.target as HTMLFormElement;
    const name = (form.elements.namedItem("name") as HTMLInputElement).value;
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;

    try {
      await register(email, password, name);
      localStorage.removeItem("onboarding_completed");
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      heading="Create your account"
      subheading="Start preparing for your exams today."
    >
      <form onSubmit={handleRegister} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name">Full Name</Label>
          <Input id="name" name="name" type="text" placeholder="e.g. Tino M" required className="bg-white" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email address</Label>
          <Input id="email" name="email" type="email" placeholder="student@example.com" required className="bg-white" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" name="password" type="password" placeholder="Min. 8 characters" required minLength={8} className="bg-white" />
        </div>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full btn-primary h-12 text-base" disabled={loading}>
          {loading ? "Creating account…" : "Create Account"}
        </Button>

        <div className="text-center pt-2">
          <span className="text-muted-foreground text-sm">Already have an account? </span>
          <Link href="/login" className="text-primary font-medium hover:underline text-sm">
            Sign in
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
}
