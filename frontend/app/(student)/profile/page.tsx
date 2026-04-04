"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function ProfilePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [level, setLevel] = useState("");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) { router.push("/login"); return; }
      setEmail(user.email ?? "");
      const { data: student } = await supabase
        .from("student").select("name, level").eq("id", user.id).single();
      setName(student?.name ?? "");
      setLevel(student?.level ?? "");
    });
  }, [router]);

  async function handleSignOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  const initials = name
    ? name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : email.slice(0, 2).toUpperCase();

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      {/* Avatar */}
      <div className="flex flex-col items-center gap-3 py-6">
        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="text-2xl font-bold text-primary">{initials}</span>
        </div>
        <div className="text-center">
          <p className="font-semibold text-lg text-foreground">{name || "Student"}</p>
          <p className="text-sm text-muted-foreground">{email}</p>
          {level && (
            <span className="mt-1 inline-block text-xs font-medium px-2.5 py-0.5 rounded-full bg-primary/10 text-primary">
              {level} Level
            </span>
          )}
        </div>
      </div>

      {/* Info card */}
      <div className="bg-card border border-border rounded-2xl divide-y divide-border">
        <div className="px-5 py-4">
          <p className="text-xs text-muted-foreground mb-0.5">Full name</p>
          <p className="text-sm font-medium text-foreground">{name || "—"}</p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-muted-foreground mb-0.5">Email</p>
          <p className="text-sm font-medium text-foreground">{email || "—"}</p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-muted-foreground mb-0.5">Level</p>
          <p className="text-sm font-medium text-foreground">{level || "—"}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-card border border-border rounded-2xl divide-y divide-border">
        <button
          onClick={handleSignOut}
          className="w-full px-5 py-4 text-left text-sm font-medium text-red-600 hover:bg-red-50 transition-colors rounded-2xl"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
