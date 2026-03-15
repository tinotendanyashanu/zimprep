"use client";

import { redirect } from "next/navigation";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

// ── Sign-out button ────────────────────────────────────────────────────────────

function SignOutButton() {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <Button variant="ghost" size="sm" onClick={handleSignOut}>
      Sign out
    </Button>
  );
}

// ── Student nav shell ──────────────────────────────────────────────────────────

function StudentShell({
  children,
  studentName,
}: {
  children: React.ReactNode;
  studentName: string;
}) {
  const pathname = usePathname();
  // Hide nav during an active exam (not on /select or /results)
  const isExamActive =
    pathname.includes("/exam/") &&
    !pathname.includes("/select") &&
    !pathname.includes("/results");

  return (
    <div className="min-h-screen bg-background">
      {!isExamActive && (
        <header className="border-b border-border bg-background sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
            <span className="font-bold text-foreground text-lg">ZimPrep</span>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">{studentName}</span>
              <SignOutButton />
            </div>
          </div>
        </header>
      )}
      <main>{children}</main>
    </div>
  );
}

// ── Layout with client-side auth guard ────────────────────────────────────────

export default function StudentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [studentName, setStudentName] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) {
        router.push("/login");
        return;
      }
      const { data: student } = await supabase
        .from("student")
        .select("name")
        .eq("id", user.id)
        .single();
      setStudentName(student?.name ?? user.email ?? "Student");
    });
  }, [router]);

  if (studentName === null) {
    // Auth check in progress — render nothing to avoid flash
    return null;
  }

  return <StudentShell studentName={studentName}>{children}</StudentShell>;
}
