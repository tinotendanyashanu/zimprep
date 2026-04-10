"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { motion, AnimatePresence } from "framer-motion";
import { StudentContext, type StudentProfile } from "@/lib/student-context";

// ── SVG icons ────────────────────────────────────────────────────────────────

function IconHome({ filled }: { filled?: boolean }) {
  return filled ? (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
      <path d="M11.47 3.84a.75.75 0 011.06 0l8.69 8.69a.75.75 0 101.06-1.06l-1.31-1.31V19.5a1.5 1.5 0 01-1.5 1.5h-5.25a.75.75 0 01-.75-.75v-4.5a.75.75 0 00-.75-.75h-1.5a.75.75 0 00-.75.75v4.5a.75.75 0 01-.75.75H4.5a1.5 1.5 0 01-1.5-1.5v-9.31L1.69 11.47a.75.75 0 00-1.06 1.06l8.69-8.69z" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955a1.126 1.126 0 011.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
    </svg>
  );
}

function IconPractice({ filled }: { filled?: boolean }) {
  return filled ? (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
      <path d="M21.731 2.269a2.625 2.625 0 00-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 000-3.712zM19.513 8.199l-3.712-3.712-8.4 8.4a5.25 5.25 0 00-1.32 2.214l-.8 2.685a.75.75 0 00.933.933l2.685-.8a5.25 5.25 0 002.214-1.32l8.4-8.4z" />
      <path d="M5.25 5.25a3 3 0 00-3 3v10.5a3 3 0 003 3h10.5a3 3 0 003-3V13.5a.75.75 0 00-1.5 0v5.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5V8.25a1.5 1.5 0 011.5-1.5h5.25a.75.75 0 000-1.5H5.25z" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
    </svg>
  );
}

function IconExam({ filled }: { filled?: boolean }) {
  return filled ? (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
      <path fillRule="evenodd" d="M7.502 6h7.128A3.375 3.375 0 0118 9.375v9.375a3 3 0 003-3V6.108c0-1.505-1.125-2.811-2.664-2.94a48.972 48.972 0 00-.673-.05A3 3 0 0015 1.5h-1.5a3 3 0 00-2.663 1.618c-.225.015-.45.032-.673.05C8.662 3.295 7.554 4.542 7.502 6zM13.5 3A1.5 1.5 0 0012 4.5h4.5A1.5 1.5 0 0015 3h-1.5z" clipRule="evenodd" />
      <path fillRule="evenodd" d="M3 9.375C3 8.339 3.84 7.5 4.875 7.5h9.75c1.036 0 1.875.84 1.875 1.875v11.25c0 1.035-.84 1.875-1.875 1.875h-9.75A1.875 1.875 0 013 20.625V9.375zm9.586 4.594a.75.75 0 00-1.172-.938l-2.476 3.096-.908-.907a.75.75 0 00-1.06 1.06l1.5 1.5a.75.75 0 001.116-.062l3-3.75z" clipRule="evenodd" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
    </svg>
  );
}

function IconProfile({ filled }: { filled?: boolean }) {
  return filled ? (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
      <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clipRule="evenodd" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  );
}

// ── Nav config ────────────────────────────────────────────────────────────────

const NAV = [
  { href: "/dashboard", label: "Home",     Icon: IconHome },
  { href: "/practice",  label: "Practice", Icon: IconPractice },
  { href: "/exam/select", label: "Exam",   Icon: IconExam },
  { href: "/profile",   label: "Profile",  Icon: IconProfile },
];

function isActive(pathname: string, href: string) {
  if (href === "/dashboard") return pathname === "/dashboard";
  if (href === "/exam/select") return pathname.startsWith("/exam");
  return pathname.startsWith(href);
}

// ── Shell ─────────────────────────────────────────────────────────────────────

function StudentShell({ children, studentName }: { children: React.ReactNode; studentName: string }) {
  const pathname = usePathname();
  const router = useRouter();

  // Hide chrome during an active exam (not select screen, not results)
  const isExamActive =
    pathname.startsWith("/exam/") &&
    !pathname.endsWith("/select") &&
    !pathname.endsWith("/results");

  async function handleSignOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  if (isExamActive) {
    return <div className="min-h-screen bg-background">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* ── Top bar (desktop + mobile header) ─────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur-md">
        <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
          {/* Logo */}
          <Link href="/dashboard" className="font-bold text-lg tracking-tight text-foreground">
            Zim<span className="text-primary">Prep</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden sm:flex items-center gap-1">
            {NAV.map(({ href, label, Icon }) => {
              const active = isActive(pathname, href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  <span className={`[&_svg]:w-4 [&_svg]:h-4 ${active ? "text-primary" : ""}`}>
                    <Icon filled={active} />
                  </span>
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Desktop right */}
          <div className="hidden sm:flex items-center gap-3">
            <span className="text-xs text-muted-foreground max-w-[160px] truncate">{studentName}</span>
            <button
              onClick={handleSignOut}
              className="text-xs text-muted-foreground hover:text-foreground px-2.5 py-1.5 rounded-lg hover:bg-muted transition-colors"
            >
              Sign out
            </button>
          </div>

          {/* Mobile: greeting */}
          <p className="sm:hidden text-sm font-medium text-foreground truncate max-w-[160px]">
            {studentName.split(" ")[0]}
          </p>
        </div>
      </header>

      {/* ── Page content ─────────────────────────────────────────────────── */}
      <main className="flex-1 pb-20 sm:pb-0 relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="h-full"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* ── Bottom tab bar (mobile only) ──────────────────────────────────── */}
      <nav className="sm:hidden fixed bottom-0 inset-x-0 z-40 bg-background/80 backdrop-blur-xl border-t border-black/5 dark:border-white/10">
        <div className="flex items-stretch h-16 safe-area-inset-bottom">
          {NAV.map(({ href, label, Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex-1 flex flex-col items-center justify-center gap-0.5 pt-2 pb-3 transition-colors ${
                  active ? "text-primary" : "text-muted-foreground"
                }`}
              >
                <span className="relative">
                  <Icon filled={active} />
                  {active && (
                    <motion.span 
                      layoutId="bottom-nav-indicator"
                      className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-primary" 
                    />
                  )}
                </span>
                <span className={`text-[10px] font-medium ${active ? "text-primary" : ""}`}>
                  {label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

// ── Layout ────────────────────────────────────────────────────────────────────

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [employeeRole, setEmployeeRole] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) { router.push("/login"); return; }

      // Check if viewer is an employee/admin (for the "back" banner)
      // Uses backend so RLS on employee table is not an issue
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        try {
          const empRes = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"}/admin/employees/me`,
            { headers: { Authorization: `Bearer ${session.access_token}` } }
          );
          if (empRes.ok) {
            const emp = await empRes.json();
            setEmployeeRole(emp.role);
          }
        } catch { /* not an employee */ }
      }

      const { data: student } = await supabase
        .from("student")
        .select("name, exam_board, level")
        .eq("id", user.id)
        .single();
      setProfile({
        id: user.id,
        name: student?.name ?? user.email ?? "Student",
        examBoard: student?.exam_board ?? "zimsec",
        level: student?.level ?? "",
      });
    });
  }, [router]);

  if (profile === null) return null;
  return (
    <StudentContext.Provider value={profile}>
      {/* Banner shown when an admin/employee is previewing the student view */}
      {employeeRole && (
        <div className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-4 py-2 bg-foreground text-background text-xs font-medium">
          <span>Viewing as student — <span className="opacity-60">preview mode</span></span>
          <Link
            href={employeeRole === "admin" ? "/admin" : "/workstation"}
            className="underline hover:no-underline"
          >
            Back to {employeeRole === "admin" ? "Admin" : "Workstation"}
          </Link>
        </div>
      )}
      <div className={employeeRole ? "pt-9" : ""}>
        <StudentShell studentName={profile.name}>{children}</StudentShell>
      </div>
    </StudentContext.Provider>
  );
}
