"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";

export default function DashboardPage() {
  const [studentName, setStudentName] = useState<string>("");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) return;
      const { data: student } = await supabase
        .from("student")
        .select("name")
        .eq("id", user.id)
        .single();
      setStudentName(student?.name ?? user.email ?? "Student");
    });
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">
          {studentName ? `Welcome back, ${studentName}` : "Welcome back"}
        </h1>
        <p className="text-muted-foreground mt-1">Ready to practise?</p>
      </div>
      <Button asChild size="lg">
        <Link href="/exam/select">Start New Exam</Link>
      </Button>
    </div>
  );
}
