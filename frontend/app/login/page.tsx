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

    const formData = new FormData(e.target as HTMLFormElement);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    try {
      // Import login function dynamically to avoid circular deps
      const { login } = await import('@/lib/auth');
      
      // Call real backend login
      await login(email, password);
      
      // Check if onboarding is done
      const onboarding = localStorage.getItem("onboarding_completed");
      if (onboarding) {
        router.push("/dashboard");
      } else {
        router.push("/onboarding");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
      setLoading(false);
    }
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
            name="email"
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
            name="password"
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
