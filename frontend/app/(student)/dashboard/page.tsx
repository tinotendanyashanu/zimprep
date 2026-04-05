"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import {
  getStudentDashboard,
  type DashboardData,
  type WeakTopic,
  type SessionSummary,
} from "@/lib/api";
import { useStudent } from "@/lib/student-context";
import { cn } from "@/lib/utils";
import { QuotaBar } from "@/components/QuotaBar";
import { PastDueBanner } from "@/components/PastDueBanner";
import { useQuota } from "@/hooks/useQuota";
import { motion, AnimatePresence } from "framer-motion";
import { Target, AlertTriangle, BookOpen, Clock, ChevronRight, CheckCircle2, XCircle, MoreVertical, Flame } from "lucide-react";

// ── Helpers ──────────────

function fmt(n: number | null | undefined) {
  return n != null ? `${n}%` : "0%";
}

function getRITagline(ri: number, subjectName: string) {
  if (ri >= 75) return `You're exceptionally prepared for ${subjectName}.`;
  if (ri >= 50) return `You're making solid progress in ${subjectName}.`;
  return `Serious practice is required for ${subjectName}.`;
}

function riColorHex(ri: number) {
  if (ri >= 75) return "#16a34a"; // green-600
  if (ri >= 50) return "#d97706"; // amber-600
  return "#dc2626";               // red-600
}

function riColorClass(ri: number) {
  if (ri >= 75) return "text-green-600 bg-green-50"; 
  if (ri >= 50) return "text-amber-600 bg-amber-50"; 
  return "text-red-600 bg-red-50";               
}

// ── Google Material Components ──

const materialCard = "bg-white border border-gray-200 rounded-xl md:rounded-2xl shadow-sm";
const cardPadding = "p-5 md:p-6";
const sectionHeader = "text-sm font-bold text-gray-800 tracking-tight uppercase px-1 mb-3";

function CircularProgress({ value, size = 180, strokeWidth = 14 }: { value: number; size?: number; strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (value / 100) * circumference;
  
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Background Track */}
      <svg className="absolute inset-0" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#f3f4f6"
          strokeWidth={strokeWidth}
        />
      </svg>
      {/* Foreground Track */}
      <svg className="absolute inset-0 transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={riColorHex(value)}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      {/* Center Label */}
      <div className="flex flex-col items-center">
        <span className="text-5xl font-extrabold tracking-tighter text-gray-900 leading-none">
          {value}
        </span>
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-500 mt-1">Index</span>
      </div>
    </div>
  );
}

// ── Main Dashboard ──────────────

export default function DashboardPage() {
  const { id: studentId, name } = useStudent();
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { quota, subscription } = useQuota();

  // Fetch auth token (needed for the authed dashboard API call)
  useEffect(() => {
    createClient().auth.getSession().then(({ data: session }) => {
      setToken(session?.session?.access_token ?? null);
    });
  }, []);

  useEffect(() => {
    if (!token) return;
    getStudentDashboard(studentId, selectedSubject, token)
      .then((d) => {
        setData(d);
        if (!selectedSubject && d.subject_id) setSelectedSubject(d.subject_id);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [studentId, token, selectedSubject]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] p-4 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-32 w-32 bg-gray-200 rounded-full mb-4" />
          <div className="h-4 w-48 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center p-8">
        <div className="bg-red-50 text-red-800 border border-red-200 p-6 rounded-xl flex items-center gap-3 w-full max-w-md">
          <AlertTriangle className="h-6 w-6 shrink-0" />
          <p className="font-medium text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const containerVars = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };
  const itemVars = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { duration: 0.3 } }
  };

  // Empty Data Flow (New Student)
  if (!data?.has_data) {
    return (
      <motion.div variants={containerVars} initial="hidden" animate="show" className="min-h-screen bg-[#F8F9FA] mx-auto max-w-xl px-4 py-16">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Welcome, {name}</h1>
          <p className="text-gray-500 mt-2">You haven't completed any sessions yet to generate a Readiness Index.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/practice" className="block">
             <div className="p-6 bg-white border border-gray-200 rounded-2xl hover:border-blue-300 hover:shadow-md transition-all active:scale-[0.98]">
              <Target className="h-8 w-8 text-blue-600 mb-4" />
              <p className="font-bold text-gray-900 text-lg">Start Practice</p>
              <p className="text-sm text-gray-500 mt-1">Adaptive learning mode</p>
            </div>
          </Link>
          <Link href="/exam/select" className="block">
             <div className="p-6 bg-white border border-gray-200 rounded-2xl hover:border-blue-300 hover:shadow-md transition-all active:scale-[0.98]">
              <Clock className="h-8 w-8 text-indigo-600 mb-4" />
              <p className="font-bold text-gray-900 text-lg">Take Exam</p>
              <p className="text-sm text-gray-500 mt-1">Timed past papers</p>
            </div>
          </Link>
        </div>
      </motion.div>
    );
  }

  const ri = data.readiness!;
  const streak = data.streak;
  const weakTopics = data.weak_topics;
  const currentSubjectName = data.subjects.find(s => s.id === selectedSubject)?.name || "All Subjects";

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-gray-900 pb-24 font-sans selection:bg-blue-100">
      <motion.div 
        variants={containerVars} 
        initial="hidden" 
        animate="show" 
        className="mx-auto max-w-2xl px-4 pt-6"
      >
        {/* Top Header Row / Navigation */}
        <motion.div variants={itemVars} className="flex items-center justify-between mb-8">
          {data.subjects.length > 1 ? (
            <div className="bg-white border border-gray-200 rounded-full px-4 py-2 shadow-sm relative flex items-center">
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="appearance-none bg-transparent text-sm font-bold text-gray-800 pr-6 outline-none cursor-pointer"
              >
                {data.subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} Context</option>
                ))}
              </select>
              <span className="absolute right-3 pointer-events-none text-gray-400">▾</span>
            </div>
          ) : (
            <span className="px-4 py-2 text-sm font-bold text-gray-800 border border-gray-200 bg-white rounded-full shadow-sm">
              {currentSubjectName}
            </span>
          )}
          
          <div className="font-medium text-sm text-gray-500">
            {name} Dashboard
          </div>
        </motion.div>

        <AnimatePresence>
          {(subscription?.status === "past_due" || quota?.limit !== null) && (
            <motion.div layout variants={itemVars} className="mb-6 space-y-3">
              {subscription && subscription.status === "past_due" && <PastDueBanner subscription={subscription} />}
              {quota && quota.limit !== null && <QuotaBar quota={quota} />}
            </motion.div>
          )}
        </AnimatePresence>

        {/* 1. Readiness Index (Primary Hero) */}
        <motion.div variants={itemVars} className="mb-10">
          <div className={cn(materialCard, cardPadding, "flex flex-col items-center justify-center text-center")}>
            <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-6">Readiness Index</h2>
            
            <CircularProgress value={ri.readiness_index} size={190} strokeWidth={16} />
            
            <div className="mt-8 mb-4 max-w-xs mx-auto">
              {/* Score Breakdown Bars */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
                    <span>Accuracy (40%)</span>
                    <span>{fmt(ri.accuracy)}</span>
                  </div>
                  <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{width: `${ri.accuracy}%`}} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
                    <span>Coverage (35%)</span>
                    <span>{fmt(ri.coverage)}</span>
                  </div>
                  <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{width: `${ri.coverage}%`}} />
                  </div>
                </div>
              </div>
            </div>

            <p className={cn("text-sm font-semibold mt-2 px-4 py-2 rounded-lg", riColorClass(ri.readiness_index))}>
              {getRITagline(ri.readiness_index, currentSubjectName)}
            </p>
          </div>
        </motion.div>

        {/* Next Actions (Clear CTAs placed immediately below context) */}
        <motion.div variants={itemVars} className="grid grid-cols-2 gap-3 mb-10">
          <Link href="/practice" className="block">
            <div className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl p-4 flex flex-col items-center justify-center shadow-sm transition-colors active:scale-[0.98]">
              <Target className="h-6 w-6 mb-2 text-blue-100" />
              <span className="font-bold text-[15px]">Start Practice</span>
            </div>
          </Link>
          <Link href="/exam/select" className="block">
            <div className="bg-white border border-gray-200 hover:bg-gray-50 text-gray-900 rounded-xl p-4 flex flex-col items-center justify-center shadow-sm transition-colors active:scale-[0.98]">
              <Clock className="h-6 w-6 mb-2 text-gray-500" />
              <span className="font-bold text-[15px]">Take Exam</span>
            </div>
          </Link>
        </motion.div>

        {/* 2. Weak Topics (Immediate Actionable Focus) */}
        <motion.div variants={itemVars} className="mb-10">
          <h2 className={sectionHeader}>Target Study Areas</h2>
          <div className={cn(materialCard, "overflow-hidden")}>
            {weakTopics.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {weakTopics.slice(0, 4).map((t) => (
                  <div key={t.topic} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-gray-900 truncate mb-1">{t.topic}</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 max-w-[120px] h-1.5 bg-red-100 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 rounded-full" style={{ width: `${t.fail_ratio * 100}%` }}/>
                        </div>
                        <span className="text-[11px] font-bold text-red-600 uppercase tracking-wide">
                          {Math.round(t.fail_ratio * 100)}% Miss Rate
                        </span>
                      </div>
                    </div>
                    <Link href={`/practice?topic=${encodeURIComponent(t.topic)}`}>
                       <button className="shrink-0 bg-blue-50 text-blue-700 hover:bg-blue-100 px-4 py-1.5 rounded-lg text-sm font-bold transition-colors w-full sm:w-auto mt-2 sm:mt-0">
                         Practice Topic
                       </button>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-500">No weak topics identified yet. Keep going!</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* 3. Active Subjects Panel */}
        <motion.div variants={itemVars} className="mb-10">
          <h2 className={sectionHeader}>Subscribed Subjects</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {data.subjects.map(s => (
              <div key={s.id} className={cn(materialCard, "p-4 flex flex-col justify-between hover:border-gray-300 transition-colors cursor-pointer")} onClick={() => setSelectedSubject(s.id)}>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-bold text-gray-900">{s.name}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">{s.level}</p>
                  </div>
                  {s.id === selectedSubject && <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">Active</span>}
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-gray-100 text-xs font-semibold text-gray-600">
                   <span>Set as active dashboard context</span>
                   <ChevronRight className="h-4 w-4" />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* 4. Syllabus Coverage */}
        {data.coverage && (
          <motion.div variants={itemVars} className="mb-10">
            <h2 className={sectionHeader}>Syllabus Gaps</h2>
            <div className={cn(materialCard, cardPadding)}>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-gray-800">Uncovered Topics ({data.coverage.uncovered.length})</span>
                <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2 py-1 rounded">{data.coverage.covered_count} / {data.coverage.total_count} covered</span>
              </div>
              
              {data.coverage.uncovered.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {data.coverage.uncovered.slice(0, 8).map(topic => (
                    <span key={topic.topic} className="bg-red-50 border border-red-100 text-red-800 text-[11px] font-bold px-3 py-1.5 rounded-md">
                      {topic.topic}
                    </span>
                  ))}
                  {data.coverage.uncovered.length > 8 && (
                    <span className="bg-gray-50 border border-gray-200 text-gray-500 text-[11px] font-bold px-3 py-1.5 rounded-md">
                      +{data.coverage.uncovered.length - 8} more
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-sm text-green-600 font-medium flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> You've attempted every topic in the syllabus!
                </p>
              )}
            </div>
          </motion.div>
        )}

        {/* 5. Recent Activity Feed */}
        <motion.div variants={itemVars} className="mb-10">
          <div className="flex items-center justify-between mb-3 px-1">
            <h2 className={cn(sectionHeader, "mb-0")}>Activity Log</h2>
            <Link href="/history" className="text-xs font-bold text-blue-600 hover:text-blue-800 uppercase tracking-widest">View All</Link>
          </div>
          <div className={cn(materialCard, "overflow-hidden")}>
             {data.recent_sessions.length === 0 ? (
                <div className="p-8 text-center bg-gray-50/50">
                  <p className="text-sm text-gray-500 font-medium">No activity logged.</p>
                </div>
             ) : (
                <div className="divide-y divide-gray-100">
                  {data.recent_sessions.slice(0, 5).map(s => {
                    const isGood = s.percentage != null && s.percentage >= 70;
                    const isBad = s.percentage != null && s.percentage < 40;
                    return (
                      <div key={s.session_id} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                             <span className="bg-gray-100 text-gray-600 text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded flex items-center gap-1">
                               {s.mode === "exam" ? <Clock className="h-3 w-3" /> : <Target className="h-3 w-3" />}
                               {s.mode}
                             </span>
                             <span className="text-xs text-gray-400 font-medium">
                               {s.completed_at ? new Date(s.completed_at).toLocaleDateString() : 'N/A'}
                             </span>
                          </div>
                          <p className="text-sm font-bold text-gray-900 truncate">
                            {s.subject_name || "Unknown"} P{s.paper_number}
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          {s.percentage != null ? (
                            <span className={cn("text-sm font-black", isGood ? "text-green-600" : isBad ? "text-red-600" : "text-amber-600")}>
                               {s.percentage}%
                            </span>
                          ) : (
                            <span className="text-sm font-black text-gray-800">{s.score}/{s.total_marks}</span>
                          )}
                          <Link href={`/exam/${s.session_id}/results`} className="text-[10px] font-bold text-blue-600 hover:underline">
                            Review Results
                          </Link>
                        </div>
                      </div>
                    )
                  })}
                </div>
             )}
          </div>
        </motion.div>

        {/* 6. Streak Tracker (Visual 7-Day Block) */}
        <motion.div variants={itemVars} className="mb-12">
          <h2 className={sectionHeader}>Consistency</h2>
          <div className={cn(materialCard, cardPadding)}>
             <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                <div>
                   <div className="flex items-center gap-2 mb-1">
                     <Flame className="h-6 w-6 text-orange-500" strokeWidth={2.5} fill="#f97316" />
                     <span className="text-2xl font-black text-gray-900">{streak.current} Days</span>
                   </div>
                   <p className="text-sm text-gray-500 font-medium">Current active streak. Longest: {streak.longest}d</p>
                </div>
                
                {/* Visual 7 Day Mock Tracker */}
                <div className="flex gap-2">
                   {[...Array(7)].map((_, i) => {
                     // Fill blocks based on streak, cap at 7
                     const isActive = i < Math.min(streak.current, 7);
                     return (
                       <div 
                         key={i} 
                         className={cn(
                           "flex-1 sm:w-10 h-10 rounded-lg border flex items-center justify-center shadow-sm",
                           isActive ? "bg-orange-50 border-orange-200 text-orange-500" : "bg-gray-50 border-gray-100 text-gray-300"
                         )}
                       >
                         {isActive && <Flame className="h-5 w-5" fill="currentColor" />}
                       </div>
                     )
                   })}
                </div>
             </div>
          </div>
        </motion.div>

      </motion.div>
    </div>
  );
}
