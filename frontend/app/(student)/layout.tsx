"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "▦" },
  { href: "/practice",  label: "Practice",  icon: "✏" },
  { href: "/exam/select", label: "Exam",    icon: "📄" },
];

function StudentShell({ children, studentName }: { children: React.ReactNode; studentName: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const isExamActive =
    pathname.includes("/exam/") && !pathname.includes("/select") && !pathname.includes("/results");

  async function handleSignOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-background">
      {!isExamActive && (
        <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-6">
            <Link href="/dashboard" className="font-bold text-foreground text-lg shrink-0">
              ZimPrep
            </Link>
            <nav className="hidden sm:flex items-center gap-1">
              {NAV.map(({ href, label }) => {
                const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href.split("/").slice(0, 2).join("/")));
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
            <div className="flex items-center gap-2 ml-auto">
              <span className="hidden sm:block text-xs text-muted-foreground truncate max-w-32">
                {studentName}
              </span>
              <button
                onClick={handleSignOut}
                className="text-xs text-muted-foreground hover:text-foreground px-2 py-1.5 rounded-md hover:bg-muted transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
          {/* Mobile nav */}
          <div className="sm:hidden flex border-t border-border">
            {NAV.map(({ href, label, icon }) => {
              const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href.split("/").slice(0, 2).join("/")));
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex-1 flex flex-col items-center py-2 text-xs font-medium transition-colors ${
                    active ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  <span className="text-base">{icon}</span>
                  {label}
                </Link>
              );
            })}
          </div>
        </header>
      )}
      <main>{children}</main>
    </div>
  );
}

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [studentName, setStudentName] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) { router.push("/login"); return; }
      const { data: student } = await supabase
        .from("student").select("name").eq("id", user.id).single();
      setStudentName(student?.name ?? user.email ?? "Student");
    });
  }, [router]);

  if (studentName === null) return null;
  return <StudentShell studentName={studentName}>{children}</StudentShell>;
}
