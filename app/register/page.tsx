"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      // Mock Registration Logic
      localStorage.setItem("isAuthenticated", "true");
      // New users always go to onboarding
      localStorage.removeItem("onboarding_completed"); 
      router.push("/onboarding");
    }, 1000);
  };

  return (
    <AuthLayout 
      heading="Create your account" 
      subheading="Start preparing for your exams today."
    >
      <form onSubmit={handleRegister} className="space-y-6">
         <div className="space-y-2">
          <Label htmlFor="name">Full Name</Label>
          <Input id="name" type="text" placeholder="e.g. Tino M" required className="bg-white" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email address</Label>
          <Input id="email" type="email" placeholder="student@example.com" required className="bg-white" />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" placeholder="Min. 8 characters" required className="bg-white" />
        </div>

        <Button type="submit" className="w-full btn-primary h-12 text-base" disabled={loading}>
          {loading ? "Creating account..." : "Create Account"}
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
