"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Simulate network delay
    setTimeout(() => {
      // Mock Auth Logic
      // In a real app, this would be an API call
      // For Phase 1: Success rate < 5% error (KPI)
      const success = Math.random() > 0.05; 

      if (success) {
        localStorage.setItem("isAuthenticated", "true");
        // Check if onboarding is done (mock)
        const onboarding = localStorage.getItem("onboarding_completed");
        if (onboarding) {
          router.push("/dashboard");
        } else {
          router.push("/onboarding");
        }
      } else {
        setError("Invalid credentials. Please try again.");
        setLoading(false);
      }
    }, 1000);
  };

  return (
    <AuthLayout 
      heading="Welcome back" 
      subheading="Sign in to continue your preparation."
    >
      <form onSubmit={handleLogin} className="space-y-6">
        <div className="space-y-2 animate-stagger-0">
          <Label htmlFor="email" className="text-zinc-600">Email address</Label>
          <Input 
            id="email" 
            type="email" 
            placeholder="student@example.com" 
            required 
            className="bg-zinc-50 border-zinc-200 focus:bg-white transition-all duration-300 h-11" 
          />
        </div>
        
        <div className="space-y-2 animate-stagger-1">
            <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-zinc-600">Password</Label>
                <Link href="/forgot-password" className="text-xs font-medium text-primary hover:underline hover:text-primary/80 transition-colors">
                    Forgot password?
                </Link>
            </div>
          <Input 
            id="password" 
            type="password" 
            required 
            className="bg-zinc-50 border-zinc-200 focus:bg-white transition-all duration-300 h-11" 
          />
        </div>

        {error && (
            <div className="text-sm text-red-500 font-medium px-2 animate-shake">{error}</div>
        )}

        <div className="pt-2 animate-stagger-2">
            <Button 
                type="submit" 
                className="w-full btn-primary h-12 text-base shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all duration-300" 
                disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in...
                </span>
              ) : "Sign in"}
            </Button>
        </div>

        <div className="text-center pt-2 animate-stagger-3">
           <span className="text-muted-foreground text-sm">Don&apos;t have an account? </span>
           <Link href="/register" className="text-primary font-medium hover:underline text-sm hover:text-primary/80 transition-colors">
             Create one
           </Link>
        </div>
      </form>
    </AuthLayout>
  );
}
