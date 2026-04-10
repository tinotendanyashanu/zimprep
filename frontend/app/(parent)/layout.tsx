"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

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

function ParentShell({
  children,
  parentName,
  employeeRole,
}: {
  children: React.ReactNode;
  parentName: string;
  employeeRole: string | null;
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* Banner shown when an admin is previewing the parent view */}
      {employeeRole && (
        <div className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-4 py-2 bg-foreground text-background text-xs font-medium">
          <span>Viewing as parent — <span className="opacity-60">preview mode</span></span>
          <Link
            href={employeeRole === "admin" ? "/admin" : "/workstation"}
            className="underline hover:no-underline"
          >
            Back to {employeeRole === "admin" ? "Admin" : "Workstation"}
          </Link>
        </div>
      )}
      <div className={employeeRole ? "pt-9" : ""}>
        <header className="sticky top-0 z-40 border-b border-border bg-background">
          <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-foreground">ZimPrep</span>
              <Badge variant="secondary">Parent Account</Badge>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">{parentName}</span>
              {!employeeRole && <SignOutButton />}
            </div>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}

export default function ParentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [parentName, setParentName] = useState<string | null>(null);
  const [employeeRole, setEmployeeRole] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) {
        router.push("/login");
        return;
      }

      // Check if viewer is an employee/admin (preview mode)
      const { data: emp } = await supabase
        .from("employee")
        .select("role")
        .eq("user_id", user.id)
        .maybeSingle();

      if (emp) {
        // Employee/admin previewing parent view — show a placeholder name
        setEmployeeRole(emp.role);
        setParentName("Parent Preview");
        setReady(true);
        return;
      }

      const { data: parent } = await supabase
        .from("parent")
        .select("name")
        .eq("id", user.id)
        .single();

      if (!parent) {
        router.push("/dashboard");
        return;
      }

      setParentName(parent.name ?? user.email ?? "Parent");
      setReady(true);
    });
  }, [router]);

  if (!ready) return null;

  return (
    <ParentShell parentName={parentName!} employeeRole={employeeRole}>
      {children}
    </ParentShell>
  );
}
