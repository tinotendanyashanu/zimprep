"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
  IGCSE: "Cambridge IGCSE",
  AS_Level: "Cambridge AS Level",
  A_Level: "Cambridge A Level",
};

const BOARD_LABELS: Record<string, string> = {
  zimsec: "ZIMSEC",
  cambridge: "Cambridge",
};

export default function ProfilePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [level, setLevel] = useState("");
  const [examBoard, setExamBoard] = useState("");

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) { router.push("/login"); return; }
      setEmail(user.email ?? "");
      const { data: student } = await supabase
        .from("student")
        .select("name, level, exam_board")
        .eq("id", user.id)
        .single();
      setName(student?.name ?? "");
      setLevel(student?.level ?? "");
      setExamBoard(student?.exam_board ?? "");
    });
  }, [router]);

  async function handleSignOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  const initials = name
    ? name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : email.slice(0, 2).toUpperCase();

  const boardLabel = BOARD_LABELS[examBoard] ?? examBoard;
  const levelLabel = LEVEL_LABELS[level] ?? level;
  const isCambridge = examBoard === "cambridge";

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
          <div className="flex items-center justify-center gap-2 mt-2 flex-wrap">
            {examBoard && (
              <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${isCambridge ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>
                {boardLabel}
              </span>
            )}
            {level && (
              <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-primary/10 text-primary">
                {levelLabel}
              </span>
            )}
          </div>
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
          <p className="text-xs text-muted-foreground mb-0.5">Exam board</p>
          <p className="text-sm font-medium text-foreground">{boardLabel || "—"}</p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs text-muted-foreground mb-0.5">Level</p>
          <p className="text-sm font-medium text-foreground">{levelLabel || "—"}</p>
        </div>
      </div>

      {/* Locked settings notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4">
        <p className="text-sm font-medium text-amber-800">Need to change your exam board or level?</p>
        <p className="text-xs text-amber-700 mt-1">
          These settings are locked after signup. Contact your admin to make changes.
        </p>
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
