"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";

export default function SignIn() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-white flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-[#065F46] rounded-lg flex items-center justify-center">
              <span className="text-sm text-white font-bold">Z</span>
            </div>
            <span className="text-lg font-bold text-zinc-900">ZimPrep</span>
          </Link>
          <h1 className="text-3xl font-bold text-zinc-900 mb-2">Welcome back</h1>
          <p className="text-zinc-600">Sign in to continue your exam preparation</p>
        </div>

        <Card className="border-zinc-200 shadow-lg">
          <CardContent className="pt-6">
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  className="w-full px-4 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#065F46]/20 focus:border-[#065F46]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full px-4 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#065F46]/20 focus:border-[#065F46]"
                />
              </div>
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" className="rounded" />
                  <span className="text-zinc-600">Remember me</span>
                </label>
                <Link href="#" className="text-[#065F46] hover:underline">
                  Forgot password?
                </Link>
              </div>
              <Button asChild className="w-full bg-[#065F46] hover:bg-[#055444]">
                <Link href="/dashboard">
                  Sign in
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </form>

            <div className="mt-6 text-center text-sm text-zinc-600">
              Don't have an account?{" "}
              <Link href="/auth/signup" className="text-[#065F46] font-medium hover:underline">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-zinc-500 mt-6">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </main>
  );
}
