"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  BookOpen,
  GraduationCap,
  School,
  ArrowRight,
  FileText,
  Sparkles,
  Loader2,
} from "lucide-react";
import { getSubjects, type Subject } from "@/lib/api";

/* ── Level config ──────────────────────────────────────────────────────────── */

const LEVEL_CONFIG: Record<
  string,
  { title: string; description: string; icon: React.ReactNode; order: number; gradient: string; badge: string }
> = {
  Grade7: {
    title: "Grade 7",
    description: "Preparation for Grade 7 final examinations.",
    icon: <School className="w-6 h-6" />,
    order: 0,
    gradient: "from-sky-500 to-cyan-400",
    badge: "bg-sky-100 text-sky-700 border-sky-200",
  },
  O: {
    title: "O-Level (Form 4)",
    description: "Core O-Level syllabus coverage.",
    icon: <BookOpen className="w-6 h-6" />,
    order: 1,
    gradient: "from-emerald-500 to-teal-400",
    badge: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  A: {
    title: "A-Level (Form 6)",
    description: "Advanced Level preparation for university entry.",
    icon: <GraduationCap className="w-6 h-6" />,
    order: 2,
    gradient: "from-purple-500 to-violet-400",
    badge: "bg-purple-100 text-purple-700 border-purple-200",
  },
  IGCSE: {
    title: "Cambridge IGCSE",
    description: "Cambridge IGCSE — internationally recognised O Level equivalent.",
    icon: <BookOpen className="w-6 h-6" />,
    order: 3,
    gradient: "from-blue-500 to-indigo-400",
    badge: "bg-blue-100 text-blue-700 border-blue-200",
  },
  AS_Level: {
    title: "Cambridge AS Level",
    description: "Cambridge International AS Level preparation.",
    icon: <GraduationCap className="w-6 h-6" />,
    order: 4,
    gradient: "from-indigo-500 to-blue-400",
    badge: "bg-indigo-100 text-indigo-700 border-indigo-200",
  },
  A_Level: {
    title: "Cambridge A Level",
    description: "Cambridge International A Level — university entry preparation.",
    icon: <GraduationCap className="w-6 h-6" />,
    order: 5,
    gradient: "from-violet-500 to-purple-400",
    badge: "bg-violet-100 text-violet-700 border-violet-200",
  },
};

const BOARD_LABELS: Record<string, string> = {
  zimsec: "🇿🇼 ZIMSEC",
  cambridge: "🎓 Cambridge",
};

/* ── Helpers ───────────────────────────────────────────────────────────────── */

function groupByLevel(subjects: Subject[]) {
  return subjects.reduce<Record<string, Subject[]>>((acc, s) => {
    (acc[s.level] ??= []).push(s);
    return acc;
  }, {});
}

/* ── Main Component ────────────────────────────────────────────────────────── */

export default function SubjectsPage() {
  const [activeBoard, setActiveBoard] = useState<string>("zimsec");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getSubjects(activeBoard)
      .then(setSubjects)
      .catch(() => setError("Failed to load subjects."))
      .finally(() => setLoading(false));
  }, [activeBoard]);

  const grouped = groupByLevel(subjects);
  const sortedLevels = Object.entries(grouped).sort(([a], [b]) => {
    return (LEVEL_CONFIG[a]?.order ?? 99) - (LEVEL_CONFIG[b]?.order ?? 99);
  });

  const totalSubjects = subjects.length;
  const liveSubjects = subjects.filter((s) => s.paper_count > 0);

  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-16">
          {/* ── Hero ──────────────────────────────────────────────────── */}
          <div className="max-w-4xl mx-auto text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary text-xs font-bold px-4 py-2 rounded-full mb-6">
              <Sparkles className="w-4 h-4" />
              {liveSubjects.length} Subject{liveSubjects.length !== 1 ? "s" : ""} Live &amp; Ready
            </div>
            <h1 className="text-calm-h1 mb-6 text-foreground">
              Subjects &amp; Coverage
            </h1>
            <p className="text-calm-body max-w-2xl mx-auto mb-8">
              Choose your exam board. Every subject below is powered by real past
              papers with examiner-style AI marking.
            </p>

            {/* Board toggle */}
            <div className="inline-flex rounded-full border border-border bg-zinc-50 p-1 gap-1">
              {Object.entries(BOARD_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActiveBoard(key)}
                  className={`px-6 py-2.5 rounded-full text-sm font-semibold transition-all ${
                    activeBoard === key
                      ? "bg-white shadow-md text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Loading State ─────────────────────────────────────── */}
          {loading && (
            <div className="max-w-4xl mx-auto flex flex-col items-center py-20">
              <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
              <p className="text-muted-foreground font-medium">
                Loading subjects…
              </p>
            </div>
          )}

          {/* ── Error State ──────────────────────────────────────── */}
          {error && !loading && (
            <div className="max-w-4xl mx-auto bg-red-50 border border-red-100 text-red-700 p-6 rounded-2xl text-center">
              <p className="font-medium">{error}</p>
              <button
                onClick={() => {
                  setLoading(true);
                  setError(null);
                  getSubjects(activeBoard)
                    .then(setSubjects)
                    .catch(() => setError("Failed to load subjects."))
                    .finally(() => setLoading(false));
                }}
                className="mt-4 px-6 py-2 bg-red-100 hover:bg-red-200 rounded-full text-sm font-bold transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {/* ── Stats Banner ─────────────────────────────────────── */}
          {!loading && !error && (
            <div className="max-w-4xl mx-auto mb-12">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  {
                    label: "Total Subjects",
                    value: totalSubjects,
                    color: "bg-blue-50 text-blue-600",
                  },
                  {
                    label: "Live & Active",
                    value: liveSubjects.length,
                    color: "bg-emerald-50 text-emerald-600",
                  },
                  {
                    label: "Past Papers",
                    value: subjects.reduce((a, b) => a + b.paper_count, 0),
                    color: "bg-amber-50 text-amber-600",
                  },
                  {
                    label: "Exam Boards",
                    value: activeBoard === "zimsec" ? "ZIMSEC" : "Cambridge",
                    color: "bg-purple-50 text-purple-600",
                  },
                ].map((stat, i) => (
                  <div
                    key={i}
                    className={`${stat.color} rounded-2xl p-5 text-center border border-transparent`}
                  >
                    <p className="text-2xl md:text-3xl font-black tracking-tight">
                      {stat.value}
                    </p>
                    <p className="text-xs font-bold uppercase tracking-widest mt-1 opacity-70">
                      {stat.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Subject Grid (Dynamically from API) ──────────────── */}
          {!loading && !error && (
            <div className="max-w-5xl mx-auto space-y-16">
              {sortedLevels.length === 0 && (
                <div className="text-center py-16">
                  <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-gray-500 mb-2">
                    No subjects yet
                  </h3>
                  <p className="text-muted-foreground">
                    We&apos;re adding {activeBoard === "zimsec" ? "ZIMSEC" : "Cambridge"} subjects soon. Check back!
                  </p>
                </div>
              )}

              {sortedLevels.map(([level, subs]) => {
                const config = LEVEL_CONFIG[level] ?? {
                  title: level,
                  description: `${level} Level subjects.`,
                  icon: <BookOpen className="w-6 h-6" />,
                  order: 99,
                  gradient: "from-gray-500 to-gray-400",
                  badge: "bg-gray-100 text-gray-600 border-gray-200",
                };
                const liveSubs = subs.filter((s) => s.paper_count > 0);
                const comingSoonSubs = subs.filter(
                  (s) => s.paper_count === 0
                );

                return (
                  <div key={level}>
                    {/* Level Header */}
                    <div className="flex items-center gap-4 mb-8 border-b border-border pb-5">
                      <div
                        className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${config.gradient} text-white flex items-center justify-center shadow-lg shadow-primary/10`}
                      >
                        {config.icon}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3 flex-wrap">
                          <h2 className="text-2xl font-bold">
                            {config.title}
                          </h2>
                          <span
                            className={`text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full border ${config.badge}`}
                          >
                            {subs.length} Subject{subs.length !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {config.description}
                        </p>
                      </div>
                    </div>

                    {/* Live Subjects */}
                    {liveSubs.length > 0 && (
                      <div className="mb-8">
                        <p className="text-xs font-black text-emerald-600 uppercase tracking-widest mb-4 flex items-center gap-2 px-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                          Available Now
                        </p>
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                          {liveSubs.map((sub) => (
                            <Link
                              key={sub.id}
                              href="/register"
                              className="group block"
                            >
                              <div className="bg-card border border-border rounded-[1.5rem] p-6 flex flex-col hover:border-primary/40 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1 transition-all duration-300 h-full relative overflow-hidden">
                                {/* Glow accent */}
                                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-primary/10 to-transparent rounded-bl-[3rem] pointer-events-none" />

                                <div className="flex justify-between items-start mb-5 relative z-10">
                                  <div>
                                    <h3 className="font-bold text-lg text-foreground group-hover:text-primary transition-colors">
                                      {sub.name}
                                    </h3>
                                    <p className="text-xs text-muted-foreground font-mono mt-0.5">
                                      {sub.exam_board.toUpperCase()} · {config.title}
                                    </p>
                                  </div>
                                  <span className="bg-emerald-100 text-emerald-700 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full border border-emerald-200 shadow-sm flex items-center gap-1.5 shrink-0">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                                    Live
                                  </span>
                                </div>

                                <div className="flex items-center gap-2 mb-5 relative z-10">
                                  <FileText className="w-4 h-4 text-primary" />
                                  <span className="text-sm font-semibold text-foreground">
                                    {sub.paper_count} Past Paper{sub.paper_count !== 1 ? "s" : ""}
                                  </span>
                                </div>

                                <div className="mt-auto flex items-center justify-between pt-4 border-t border-border/50 relative z-10">
                                  <span className="text-xs font-bold text-primary group-hover:underline flex items-center gap-1">
                                    Start Practicing
                                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                                  </span>
                                  <span className="text-[10px] font-bold text-muted-foreground bg-muted px-2.5 py-1 rounded-full">
                                    AI Marking
                                  </span>
                                </div>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Coming Soon Subjects */}
                    {comingSoonSubs.length > 0 && (
                      <div>
                        <p className="text-xs font-black text-muted-foreground uppercase tracking-widest mb-4 flex items-center gap-2 px-1">
                          <span className="w-2 h-2 rounded-full bg-zinc-400" />
                          Coming Soon
                        </p>
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {comingSoonSubs.map((sub) => (
                            <div
                              key={sub.id}
                              className="bg-zinc-50 border border-border/60 rounded-[1.5rem] p-5 flex flex-col opacity-70 hover:opacity-90 transition-opacity"
                            >
                              <div className="flex justify-between items-start mb-3">
                                <div>
                                  <h3 className="font-bold text-base text-foreground">
                                    {sub.name}
                                  </h3>
                                  <p className="text-xs text-muted-foreground font-mono mt-0.5">
                                    {sub.exam_board.toUpperCase()}
                                  </p>
                                </div>
                                <span className="bg-zinc-200 text-zinc-600 text-[10px] font-bold px-2.5 py-1 rounded-full">
                                  Soon
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground mt-auto">
                                Papers being prepared. Notify me when ready →
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* ── Compliance Banner ─────────────────────────────────── */}
          {!loading && !error && (
            <div className="max-w-3xl mx-auto mt-20 p-6 bg-blue-50 border border-blue-100 rounded-2xl flex items-start gap-4">
              <CheckCircle2 className="w-6 h-6 text-blue-600 shrink-0 mt-1" />
              <div>
                <h4 className="font-bold text-blue-900 mb-1">
                  Aligned to Official Syllabuses
                </h4>
                <p className="text-sm text-blue-800/80 leading-relaxed">
                  {activeBoard === "zimsec"
                    ? "All ZIMSEC content is strictly aligned to the latest Zimbabwe School Examinations Council curriculum. Everything is tailored for the Zimbabwean student — no generic international content."
                    : "All Cambridge content is aligned to the latest Cambridge Assessment International Education (CAIE) syllabuses. Papers and marking follow Cambridge examiner standards."}
                </p>
              </div>
            </div>
          )}

          {/* ── CTA Section ──────────────────────────────────────── */}
          {!loading && !error && liveSubjects.length > 0 && (
            <div className="max-w-3xl mx-auto mt-16 text-center">
              <div className="bg-gradient-to-br from-primary to-emerald-700 rounded-[2rem] p-10 md:p-14 text-white relative overflow-hidden shadow-2xl shadow-primary/20">
                <div className="absolute -top-20 -right-20 w-60 h-60 bg-white/10 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-emerald-300/20 rounded-full blur-2xl pointer-events-none" />
                <div className="relative z-10">
                  <h3 className="text-2xl md:text-3xl font-bold tracking-tight mb-4">
                    Ready to start practicing?
                  </h3>
                  <p className="text-emerald-100 mb-8 text-lg max-w-md mx-auto leading-relaxed">
                    Join thousands of students preparing with real past papers and
                    examiner-style AI marking.
                  </p>
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 bg-white text-primary font-bold text-lg px-8 py-4 rounded-full hover:bg-emerald-50 transition-colors shadow-xl hover:shadow-2xl hover:-translate-y-0.5 transition-all"
                  >
                    Start Free Trial
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>

      <footer className="py-12 px-6 border-t border-border mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <Link
              href="/"
              className="text-lg font-bold tracking-tight text-foreground"
            >
              ZimPrep
            </Link>
            <nav className="flex gap-6 text-sm font-medium text-muted-foreground">
              <Link href="#" className="hover:text-foreground">
                Privacy
              </Link>
              <Link href="#" className="hover:text-foreground">
                Terms
              </Link>
              <Link href="#" className="hover:text-foreground">
                Twitter
              </Link>
            </nav>
          </div>
          <p className="text-sm text-muted-foreground w-full md:w-auto text-center md:text-right">
            &copy; 2025 ZimPrep Inc.
          </p>
        </div>
      </footer>
    </div>
  );
}
