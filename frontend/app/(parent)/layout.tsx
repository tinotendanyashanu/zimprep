"use client";

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
}: {
  children: React.ReactNode;
  parentName: string;
}) {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-foreground">ZimPrep</span>
            <Badge variant="secondary">Parent Account</Badge>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{parentName}</span>
            <SignOutButton />
          </div>
        </div>
      </header>
      <main>{children}</main>
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

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) {
        router.push("/login");
        return;
      }
      const { data: parent } = await supabase
        .from("parent")
        .select("name")
        .eq("id", user.id)
        .single();
      if (!parent) {
        // Not a parent account — redirect to student dashboard
        router.push("/dashboard");
        return;
      }
      setParentName(parent.name ?? user.email ?? "Parent");
    });
  }, [router]);

  if (parentName === null) return null;

  return <ParentShell parentName={parentName}>{children}</ParentShell>;
}
