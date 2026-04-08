"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getSubjects,
  getPapersForSubject,
  createSession,
  type Subject,
  type Paper,
} from "@/lib/api";
import { useStudent } from "@/lib/student-context";
import { EmptyState } from "@/components/empty-state";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { ChevronLeft, Compass, Clock, Play, BookOpen, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";

const premiumCard = "bg-white rounded-[2rem] ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgba(0,0,0,0.04)]";

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
};

const containerVars = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } }
} as const;

const itemVars = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
} as const;

export default function ExamSelectPage() {
  const router = useRouter();
  const { id: studentId, examBoard, level } = useStudent();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [mode, setMode] = useState<"exam" | "practice">("exam");
  const [loading, setLoading] = useState(true);
  const [papersLoading, setPapersLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getSubjects(examBoard || undefined, level || undefined)
      .then(setSubjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [examBoard, level]);

  async function handleSelectSubject(subject: Subject) {
    setSelectedSubject(subject);
    setSelectedPaper(null);
    setPapersLoading(true);
    setError(null);
    try {
      const data = await getPapersForSubject(subject.id);
      setPapers(data);
      setStep(2);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPapersLoading(false);
    }
  }

  async function handleConfirm() {
    if (!studentId) {
      setError("Could not identify your account — please sign in again.");
      return;
    }
    if (!selectedPaper) return;

    setConfirming(true);
    setError(null);
    try {
      const { session_id } = await createSession(studentId, selectedPaper.id, mode);
      router.push(`/exam/${session_id}`);
    } catch (e) {
      setError((e as Error).message);
      setConfirming(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] px-6 py-12 flex justify-center">
        <div className="max-w-3xl w-full animate-pulse space-y-4">
          <div className="h-20 rounded-3xl bg-gray-200/50" />
          <div className="grid sm:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 rounded-3xl bg-gray-200/50" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && step === 1) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] px-6 py-12 flex justify-center">
        <div className="max-w-xl w-full">
          <div className={cn(premiumCard, "p-10 text-center flex flex-col items-center")}>
             <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
             <h2 className="text-xl font-black text-gray-900 mb-2">Failed to Load</h2>
             <p className="text-gray-500 font-medium mb-6">{error}</p>
             <button
               onClick={() => {
                 setError(null);
                 setLoading(true);
                 getSubjects(examBoard || undefined, level || undefined)
                   .then(setSubjects).catch((e) => setError(e.message)).finally(() => setLoading(false));
               }}
               className="bg-black text-white px-6 py-3 rounded-xl font-bold active:scale-95 transition-all"
             >
               Try Again
             </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA] px-6 py-10 lg:py-16 selection:bg-purple-100">
      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* Step Indicator Pill */}
        <div className="flex justify-center mb-8">
           <div className="bg-white p-1 rounded-full ring-1 ring-black/5 shadow-sm inline-flex items-center gap-1">
             {(["Subject", "Paper", "Confirm"] as const).map((label, i) => (
               <div
                 key={label}
                 className={cn(
                   "px-4 py-2 rounded-full text-xs font-black uppercase tracking-widest transition-all",
                   step === i + 1
                     ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/20"
                     : step > i + 1 
                       ? "text-indigo-600 bg-indigo-50"
                       : "text-gray-400"
                 )}
               >
                 <span className="hidden sm:inline">{label}</span>
                 <span className="sm:hidden">{i+1}</span>
               </div>
             ))}
           </div>
        </div>

        {/* Step 1 — Subject selection */}
        {step === 1 && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-8">
            <motion.div variants={itemVars} className="text-center sm:text-left flex flex-col sm:flex-row items-center gap-6">
              <div className="w-16 h-16 bg-indigo-100 rounded-[1.5rem] flex items-center justify-center text-indigo-600 shrink-0 shadow-inner">
                 <Compass className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-black text-gray-900 tracking-tight">Choose Subject</h1>
                <p className="text-gray-500 font-medium text-lg mt-1">Select the discipline you want to test on.</p>
              </div>
            </motion.div>

            {subjects.length === 0 ? (
              <motion.div variants={itemVars}>
                <EmptyState
                  title="No subjects available"
                  description="Check back soon — content is being added."
                />
              </motion.div>
            ) : (
              <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {subjects.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelectSubject(s)}
                    disabled={papersLoading}
                    className={cn(premiumCard, "text-left p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group hover:scale-[1.02] active:scale-[0.98] transition-all hover:ring-indigo-500/20 outline-none")}
                  >
                    <div className="flex-1">
                      <p className="font-extrabold text-lg text-gray-900 group-hover:text-indigo-600 transition-colors leading-tight">
                        {s.name}
                      </p>
                      <p className="text-sm font-semibold text-gray-400 mt-1">
                        {s.paper_count} paper{s.paper_count !== 1 ? "s" : ""} available
                      </p>
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest bg-gray-100 text-gray-500 px-3 py-1.5 rounded-xl shrink-0 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                      {LEVEL_LABELS[s.level] ?? s.level}
                    </span>
                  </button>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Step 2 — Paper selection */}
        {step === 2 && selectedSubject && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-8">
            <motion.div variants={itemVars} className="flex items-center gap-4">
              <button
                onClick={() => setStep(1)}
                className="w-12 h-12 rounded-full bg-white ring-1 ring-black/5 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all active:scale-95"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <div>
                <h1 className="text-3xl font-black text-gray-900 tracking-tight">{selectedSubject.name}</h1>
                <p className="text-gray-500 font-medium text-lg mt-1">Select a specific paper variant</p>
              </div>
            </motion.div>

            {papersLoading ? (
              <motion.div variants={itemVars} className="animate-pulse space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-20 rounded-[1.5rem] bg-gray-200/50" />
                ))}
              </motion.div>
            ) : papers.length === 0 ? (
              <motion.div variants={itemVars}>
                <EmptyState
                  title="No discrete papers available"
                  description="Try a different subject."
                />
              </motion.div>
            ) : (
              <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {papers.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      setSelectedPaper(p);
                      setStep(3);
                    }}
                    className={cn(premiumCard, "p-6 flex flex-col text-left group hover:scale-[1.02] active:scale-[0.98] transition-all hover:ring-indigo-500/20 outline-none")}
                  >
                     <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                        <BookOpen className="w-6 h-6" />
                     </div>
                     <p className="font-extrabold text-xl text-gray-900 group-hover:text-indigo-600 transition-colors">
                        {p.year} {p.exam_session && <span className="capitalize text-gray-500 font-semibold group-hover:text-indigo-400">({p.exam_session})</span>}
                     </p>
                     <p className="font-semibold text-gray-500 mt-1 mb-4 flex-1">
                        Paper {p.paper_number}
                     </p>
                     <div className="flex justify-end">
                       <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
                     </div>
                  </button>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Step 3 — Confirm */}
        {step === 3 && selectedSubject && selectedPaper && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-8">
            <motion.div variants={itemVars} className="flex items-center gap-4">
              <button
                onClick={() => setStep(2)}
                className="w-12 h-12 rounded-full bg-white ring-1 ring-black/5 shadow-sm flex items-center justify-center text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all active:scale-95"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <div>
                <h1 className="text-3xl font-black text-gray-900 tracking-tight">Mission Brief</h1>
                <p className="text-gray-500 font-medium text-lg mt-1">Configure your run parameters</p>
              </div>
            </motion.div>

            <motion.div variants={itemVars} className={cn(premiumCard, "p-8 sm:p-10 bg-gradient-to-br from-white to-indigo-50/50")}>
              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
                 <div className="flex-1 space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500 bg-indigo-50 px-3 py-1.5 rounded-xl w-fit">Target Logged</p>
                    <p className="text-2xl font-black text-gray-900">{selectedSubject.name}</p>
                    <p className="text-lg font-bold text-gray-500">
                      {selectedPaper.year}
                      {selectedPaper.exam_session && <span className="capitalize"> ({selectedPaper.exam_session})</span>}
                      {" — "}Paper {selectedPaper.paper_number}
                    </p>
                 </div>
              </div>
              
              <div className="mt-10 mb-8 w-full h-px bg-gray-100" />

              <div className="space-y-4">
                <p className="text-xs font-black uppercase tracking-widest text-gray-400">Select Mode</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {(["exam", "practice"] as const).map((m) => {
                    const isExam = m === "exam";
                    return (
                      <button
                        key={m}
                        onClick={() => setMode(m)}
                        className={cn(
                          "rounded-3xl p-6 text-left transition-all border-2 outline-none group",
                          mode === m
                            ? "border-indigo-500 bg-indigo-50/50 shadow-md shadow-indigo-500/10 scale-[1.02]"
                            : "border-gray-100 bg-white hover:border-indigo-200 hover:bg-gray-50 hover:scale-[1.01]"
                        )}
                      >
                        <div className="flex items-center justify-between mb-3">
                           <div className={cn("w-10 h-10 rounded-2xl flex items-center justify-center shadow-sm", isExam ? "bg-red-100 text-red-600" : "bg-emerald-100 text-emerald-600")}>
                             {isExam ? <Clock className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
                           </div>
                           <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors", mode === m ? "border-indigo-500 text-indigo-500" : "border-gray-200 text-transparent")}>
                              <div className={cn("w-2.5 h-2.5 bg-current rounded-full", mode === m ? "scale-100" : "scale-0")}/>
                           </div>
                        </div>
                        <p className={cn("font-extrabold text-xl mb-1", mode === m ? "text-indigo-900" : "text-gray-800")}>{isExam ? "Exam Cond." : "Practice"}</p>
                        <p className="text-sm font-semibold text-gray-500 leading-relaxed">
                          {isExam
                            ? "Strict timing. Full submission at end. No assist."
                            : "Instant AI feedback per question to master concepts."}
                        </p>
                      </button>
                    )
                  })}
                </div>
              </div>

              {error && (
                <p className="text-sm font-bold text-red-600 mt-6 bg-red-50 p-4 rounded-xl">{error}</p>
              )}

              <div className="mt-10">
                <button
                  onClick={handleConfirm}
                  disabled={confirming}
                  className="w-full py-5 rounded-[1.5rem] bg-gray-900 hover:bg-black text-white font-black text-lg transition-all active:scale-95 shadow-xl shadow-black/20 flex items-center justify-center gap-3 disabled:opacity-50 disabled:scale-100"
                >
                  {confirming ? (
                    <><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Initializing...</>
                  ) : (
                    <><Play className="w-5 h-5 fill-current" /> Commense Run</>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
