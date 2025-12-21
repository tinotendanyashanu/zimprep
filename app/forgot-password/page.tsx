"use client";

import Link from "next/link";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  return (
    <AuthLayout 
      heading="Reset Password" 
      subheading="Enter your email to receive recovery instructions."
    >
      <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
        <div className="space-y-2">
          <Label htmlFor="email">Email address</Label>
          <Input id="email" type="email" placeholder="student@example.com" required className="bg-white" />
        </div>

        <Button type="submit" className="w-full btn-primary h-12 text-base">
          Send Recovery Email
        </Button>

        <div className="text-center pt-2">
           <Link href="/login" className="text-muted-foreground hover:text-foreground text-sm font-medium">
             Back to login
           </Link>
        </div>
      </form>
    </AuthLayout>
  );
}
