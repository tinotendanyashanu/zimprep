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

import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";

const premiumCard = "glass-card";

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
      <div className="min-h-screen bg-background px-6 py-12 flex justify-center items-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-sm font-medium text-muted-foreground animate-pulse">Loading subjects...</p>
        </div>
      </div>
    );
  }

  if (error && step === 1) {
    return (
      <div className="min-h-screen bg-background px-6 py-12 flex justify-center items-center">
        <GlassCard className="max-w-md w-full p-10 text-center flex flex-col items-center border-red-500/20 bg-red-500/5">
           <AlertCircle className="w-16 h-16 text-red-500 mb-6" />
           <h2 className="text-2xl font-bold text-foreground mb-2">Sync Failed</h2>
           <p className="text-muted-foreground font-medium mb-8 leading-relaxed">{error}</p>
           <Button
             onClick={() => {
               setError(null);
               setLoading(true);
               getSubjects(examBoard || undefined, level || undefined)
                 .then(setSubjects).catch((e) => setError(e.message)).finally(() => setLoading(false));
             }}
             className="w-full"
           >
             Try Again
           </Button>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-6 py-10 lg:py-16 font-sans">
      <div className="max-w-4xl mx-auto space-y-12">
        
        {/* Step Indicator Pill */}
        <div className="flex justify-center">
           <div className="glass p-1.5 rounded-full inline-flex items-center gap-1 shadow-2xl shadow-black/5 border-white/20 dark:border-white/5">
             {(["Subject", "Paper", "Confirm"] as const).map((label, i) => {
               const isActive = step === i + 1;
               const isCompleted = step > i + 1;
               return (
                 <div
                   key={label}
                   className={cn(
                     "px-6 py-2.5 rounded-full text-[11px] font-bold uppercase tracking-[0.2em] transition-all duration-500 flex items-center gap-2",
                     isActive
                       ? "bg-primary text-white shadow-lg shadow-primary/20 scale-105"
                       : isCompleted
                         ? "text-primary bg-primary/10"
                         : "text-muted-foreground opacity-50"
                   )}
                 >
                   <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-[10px]">
                     {isCompleted ? <CheckCircle2 className="w-3 h-3" /> : i + 1}
                   </span>
                   <span className="hidden sm:inline">{label}</span>
                 </div>
               );
             })}
           </div>
        </div>

        {/* Step 1 — Subject selection */}
        {step === 1 && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-10">
            <motion.div variants={itemVars} className="text-center sm:text-left flex flex-col sm:flex-row items-center gap-8">
              <div className="w-20 h-20 bg-primary/10 rounded-[2rem] flex items-center justify-center text-primary shrink-0 shadow-xl shadow-primary/5 group transition-transform hover:scale-105">
                 <Compass className="w-10 h-10" />
              </div>
              <div className="space-y-2">
                <h1 className="text-4xl font-bold text-foreground tracking-tight">Choose Subject</h1>
                <p className="text-muted-foreground font-medium text-lg leading-relaxed">Select the discipline you want to master today.</p>
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
              <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {subjects.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelectSubject(s)}
                    disabled={papersLoading}
                    className="group outline-none"
                  >
                    <GlassCard className="text-left p-8 flex flex-col justify-between h-full group-hover:bg-primary/5 group-hover:border-primary/20 transition-all duration-500 relative overflow-hidden group-active:scale-95">
                      <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <BookOpen className="w-20 h-20 -rotate-12" />
                      </div>
                      <div className="space-y-4 relative z-10">
                        <span className="text-[10px] font-bold uppercase tracking-[0.2em] bg-primary/10 text-primary px-3 py-1.5 rounded-full">
                          {LEVEL_LABELS[s.level] ?? s.level}
                        </span>
                        <h3 className="font-bold text-2xl text-foreground group-hover:text-primary transition-colors leading-tight pt-2">
                          {s.name}
                        </h3>
                        <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                          <Activity className="w-3 h-3" />
                          {s.paper_count} Paper{s.paper_count !== 1 ? "s" : ""}
                        </p>
                      </div>
                      <div className="mt-8 flex justify-end">
                        <div className="w-10 h-10 rounded-full border border-muted/20 flex items-center justify-center group-hover:bg-primary group-hover:text-white group-hover:border-primary transition-all duration-500">
                          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </div>
                      </div>
                    </GlassCard>
                  </button>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Step 2 — Paper selection */}
        {step === 2 && selectedSubject && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-10">
            <motion.div variants={itemVars} className="flex flex-col sm:flex-row items-center gap-8">
              <button
                onClick={() => setStep(1)}
                className="w-16 h-16 rounded-[1.5rem] bg-white dark:bg-black/40 border border-muted/10 shadow-xl flex items-center justify-center text-muted-foreground hover:text-primary hover:bg-primary/5 transition-all active:scale-90"
              >
                <ChevronLeft className="w-8 h-8" />
              </button>
              <div className="text-center sm:text-left space-y-2">
                <h1 className="text-4xl font-bold text-foreground tracking-tight">{selectedSubject.name}</h1>
                <p className="text-muted-foreground font-medium text-lg">Select a specific year and session to begin.</p>
              </div>
            </motion.div>

            {papersLoading ? (
              <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-48 rounded-[2rem] bg-muted/10 animate-pulse" />
                ))}
              </motion.div>
            ) : papers.length === 0 ? (
              <motion.div variants={itemVars}>
                <EmptyState
                  title="No papers available"
                  description="Try a different subject."
                />
              </motion.div>
            ) : (
              <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {papers.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      setSelectedPaper(p);
                      setStep(3);
                    }}
                    className="group outline-none"
                  >
                    <GlassCard className="p-8 flex flex-col text-left h-full group-hover:bg-indigo-500/5 group-hover:border-indigo-500/20 transition-all duration-500 group-active:scale-95">
                       <div className="w-14 h-14 bg-indigo-500/10 text-indigo-500 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-indigo-500 group-hover:text-white transition-all duration-500 shadow-xl shadow-indigo-500/10">
                          <BookOpen className="w-7 h-7" />
                       </div>
                       <div className="space-y-2 flex-1">
                         <h3 className="font-bold text-2xl text-foreground group-hover:text-indigo-600 transition-colors">
                            {p.year}
                         </h3>
                         <p className="font-bold text-muted-foreground uppercase tracking-widest text-xs">
                           Paper {p.paper_number}
                           {p.exam_session && <span className="ml-2 opacity-60">• {p.exam_session}</span>}
                         </p>
                       </div>
                       <div className="mt-8 flex justify-between items-center">
                         <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">Select Paper</span>
                         <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
                       </div>
                    </GlassCard>
                  </button>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Step 3 — Confirm */}
        {step === 3 && selectedSubject && selectedPaper && (
          <motion.div variants={containerVars} initial="hidden" animate="show" className="space-y-10 max-w-2xl mx-auto">
            <motion.div variants={itemVars} className="flex items-center gap-6">
              <button
                onClick={() => setStep(2)}
                className="w-14 h-14 rounded-2xl bg-white dark:bg-black/40 border border-muted/10 shadow-xl flex items-center justify-center text-muted-foreground hover:text-indigo-500 hover:bg-indigo-500/5 transition-all active:scale-90"
              >
                <ChevronLeft className="w-7 h-7" />
              </button>
              <div className="space-y-1">
                <h1 className="text-3xl font-bold text-foreground tracking-tight">Mission Brief</h1>
                <p className="text-muted-foreground font-medium text-base">Configure your run parameters</p>
              </div>
            </motion.div>

            <GlassCard className="p-10 md:p-12 overflow-hidden relative shadow-2xl shadow-indigo-500/10 border-indigo-500/20">
              {/* Background accent */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[80px] -z-10 rounded-full" />
              
              <div className="flex flex-col gap-8">
                 <div className="space-y-4">
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-500 bg-indigo-500/10 px-4 py-1.5 rounded-full border border-indigo-500/10">Target Logged</span>
                    <div>
                      <h2 className="text-4xl font-bold text-foreground">{selectedSubject.name}</h2>
                      <p className="text-xl font-medium text-muted-foreground mt-2">
                        {selectedPaper.year}
                        {selectedPaper.exam_session && <span className="capitalize"> {selectedPaper.exam_session} Session</span>}
                        {" • "}Paper {selectedPaper.paper_number}
                      </p>
                    </div>
                 </div>

                 <div className="h-px bg-muted/10 w-full" />

                 <div className="space-y-6">
                    <p className="text-xs font-bold uppercase tracking-[0.25em] text-muted-foreground opacity-60">Select Run Mode</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      {(["exam", "practice"] as const).map((m) => {
                        const isExam = m === "exam";
                        const active = mode === m;
                        return (
                          <button
                            key={m}
                            onClick={() => setMode(m)}
                            className={cn(
                              "rounded-[2rem] p-8 text-left transition-all duration-500 border-2 outline-none group relative overflow-hidden",
                              active
                                ? "border-indigo-500 bg-indigo-500/5 shadow-xl shadow-indigo-500/10 scale-[1.05]"
                                : "border-muted/10 bg-muted/5 hover:border-indigo-500/30 hover:bg-indigo-500/[0.02]"
                            )}
                          >
                            <div className="flex items-center justify-between mb-6">
                               <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg transition-transform duration-500 group-hover:scale-110", isExam ? "bg-red-500/10 text-red-500" : "bg-emerald-500/10 text-emerald-500")}>
                                 {isExam ? <Clock className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
                               </div>
                               <div className={cn("w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-500", active ? "border-indigo-500 bg-indigo-500 shadow-lg shadow-indigo-500/30" : "border-muted/20")}>
                                  {active && <div className="w-2.5 h-2.5 bg-white rounded-full shadow-inner animate-in zoom-in-50" />}
                               </div>
                            </div>
                            <h4 className={cn("font-bold text-2xl mb-2 transition-colors duration-500", active ? "text-foreground" : "text-muted-foreground")}>{isExam ? "Exam Cond." : "Adaptive"}</h4>
                            <p className="text-sm font-medium text-muted-foreground leading-relaxed opacity-80">
                              {isExam
                                ? "Strict timing. No assistance. True test of grit."
                                : "Instant AI feedback per question to master concepts."}
                            </p>
                          </button>
                        )
                      })}
                    </div>
                 </div>

                 {error && (
                   <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-red-500/10 border border-red-500/20 p-4 rounded-2xl flex items-center gap-3 text-red-500">
                     <AlertCircle className="w-5 h-5" />
                     <p className="text-sm font-bold">{error}</p>
                   </motion.div>
                 )}

                 <div className="pt-6">
                    <Button
                      onClick={handleConfirm}
                      disabled={confirming}
                      size="lg"
                      className="w-full text-xl h-18 group"
                    >
                      {confirming ? (
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                          <span>Initializing...</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <Play className="w-6 h-6 fill-current group-hover:scale-110 transition-transform" />
                          <span>Commence Run</span>
                        </div>
                      )}
                    </Button>
                    <p className="text-center text-[10px] font-bold text-muted-foreground uppercase tracking-[0.3em] mt-6 opacity-40">System ready for deployment</p>
                 </div>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
