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
import { 
  Target, 
  AlertTriangle, 
  BookOpen, 
  Clock, 
  ChevronRight, 
  CheckCircle2, 
  TrendingDown, 
  Flame,
  Award,
  Activity,
  ArrowRight,
  Compass
} from "lucide-react";

// ── Helpers ──────────────

function fmt(n: number | null | undefined) {
  return n != null ? `${n}%` : "0%";
}

function getRITagline(ri: number, subjectName: string) {
  if (ri >= 75) return `You're mastering ${subjectName}. Keep up the great work!`;
  if (ri >= 50) return `Solid progress in ${subjectName}. A little more practice to go.`;
  return `More practice needed for ${subjectName}. Let's get to work!`;
}

function riColorHex(ri: number) {
  if (ri >= 75) return "#10b981"; // emerald-500
  if (ri >= 50) return "#f59e0b"; // amber-500
  return "#ef4444";               // red-500
}

function riColorClass(ri: number) {
  if (ri >= 75) return "text-emerald-700 bg-emerald-50"; 
  if (ri >= 50) return "text-amber-700 bg-amber-50"; 
  return "text-red-700 bg-red-50";               
}

// ── Shared Styling constants ──
const premiumCard = "bg-white rounded-3xl ring-1 ring-black/[0.04] shadow-[0_8px_30px_rgba(0,0,0,0.04)]";
const cardPadding = "p-6 md:p-8";
const sectionHeader = "text-xl font-extrabold text-gray-900 tracking-tight mb-4 flex items-center gap-2 px-1";

function CircularProgress({ value, size = 160, strokeWidth = 12 }: { value: number; size?: number; strokeWidth?: number }) {
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
        <span className="text-4xl font-extrabold tracking-tighter text-gray-900 leading-none">
          {value}
        </span>
        <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mt-1">Level</span>
      </div>
    </div>
  );
}

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
        <div className="bg-red-50 text-red-800 border border-red-200 p-6 rounded-3xl flex items-center gap-3 w-full max-w-md shadow-sm">
          <AlertTriangle className="h-6 w-6 shrink-0" />
          <p className="font-medium text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const containerVars = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } }
  } as const;
  const itemVars = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  } as const;

  // Empty Data Flow (New Student)
  if (!data?.has_data) {
    return (
      <motion.div variants={containerVars} initial="hidden" animate="show" className="min-h-screen bg-[#F8F9FA] mx-auto max-w-xl px-6 py-20">
        <motion.div variants={itemVars} className="text-center mb-12">
          <div className="w-20 h-20 bg-blue-100 rounded-[2rem] flex items-center justify-center mx-auto mb-6 text-blue-600">
             <Target className="h-10 w-10" />
          </div>
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Welcome, {name}</h1>
          <p className="text-gray-500 font-medium mt-3 text-lg leading-relaxed">You haven't completed any sessions yet. Run through your first practice module to generate your rank.</p>
        </motion.div>
        
        <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link href="/practice" className="block">
             <div className="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.04)] ring-1 ring-black/5 hover:scale-[1.02] active:scale-[0.98] transition-all flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-4">
                 <Target className="h-7 w-7" />
              </div>
              <p className="font-extrabold text-gray-900 text-lg mb-1">Start Practice</p>
              <p className="text-sm font-medium text-gray-500">Adaptive learning mode</p>
            </div>
          </Link>
          <Link href="/exam/select" className="block">
             <div className="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.04)] ring-1 ring-black/5 hover:scale-[1.02] active:scale-[0.98] transition-all flex flex-col items-center text-center">
              <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mb-4">
                <Clock className="h-7 w-7" />
              </div>
              <p className="font-extrabold text-gray-900 text-lg mb-1">Take Exam</p>
              <p className="text-sm font-medium text-gray-500">Timed past papers</p>
            </div>
          </Link>
        </motion.div>
      </motion.div>
    );
  }

  const ri = data.readiness!;
  const streak = data.streak;
  const weakTopics = data.weak_topics;
  const currentSubjectName = data.subjects.find(s => s.id === selectedSubject)?.name || "All Subjects";

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-gray-900 pb-28 font-sans selection:bg-blue-100/50">
      <motion.div 
        variants={containerVars} 
        initial="hidden" 
        animate="show" 
        className="mx-auto max-w-3xl px-6 pt-8"
      >
        {/* Top Header Row / Navigation */}
        <motion.div variants={itemVars} className="flex items-center justify-between mb-8">
          {data.subjects.length > 1 ? (
            <div className="bg-white ring-1 ring-black/5 rounded-full pl-5 pr-2 py-1.5 shadow-sm relative flex items-center hover:shadow-md transition-shadow">
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="appearance-none bg-transparent text-sm font-extrabold text-gray-800 pr-8 outline-none cursor-pointer w-full z-10"
              >
                {data.subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} Context</option>
                ))}
              </select>
              <div className="absolute right-3 w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center pointer-events-none">
                 <ChevronRight className="h-3 w-3 text-gray-500 rotate-90" />
              </div>
            </div>
          ) : (
            <span className="px-5 py-2 text-sm font-extrabold text-gray-800 bg-white ring-1 ring-black/5 rounded-full shadow-sm">
              {currentSubjectName}
            </span>
          )}
          
          <div className="font-bold text-sm text-gray-400 bg-white/50 px-4 py-2 rounded-full hidden sm:block">
            {name}'s Dashboard
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

        {/* 1. Master Hero Section */}
        <motion.div variants={itemVars} className="mb-8">
          <div className="bg-gradient-to-br from-primary to-emerald-700 rounded-[2.5rem] p-8 md:p-10 text-white relative overflow-hidden shadow-2xl shadow-primary/20">
            {/* Soft background aesthetic blurs */}
            <div className="absolute -top-20 -right-20 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-emerald-300/20 rounded-full blur-2xl pointer-events-none" />
            
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center md:items-end gap-10">
              <div className="flex-1 text-center md:text-left">
                <span className="inline-block px-4 py-1.5 rounded-full bg-white/20 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest mb-6">
                  Player Overview
                </span>
                <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4 leading-tight">
                  {ri.readiness_index >= 75 ? "Keep it up, Scholar!" : ri.readiness_index >= 50 ? "Making solid progress!" : "Time to level up!"}
                </h1>
                <p className="text-emerald-50/90 text-base md:text-lg font-medium max-w-sm mx-auto md:mx-0 leading-relaxed mb-8">
                  {getRITagline(ri.readiness_index, currentSubjectName)}
                </p>
                
                {/* Stats Pills row */}
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                  <div className="bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl flex items-center gap-3 border border-white/10">
                    <Flame className="h-6 w-6 text-orange-400 drop-shadow-md" fill="currentColor" />
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-black leading-none mb-1">{streak.current} Days</span>
                      <span className="text-[10px] font-bold text-emerald-100 uppercase tracking-widest">Active Streak</span>
                    </div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl flex items-center gap-3 border border-white/10">
                    <Award className="h-6 w-6 text-emerald-400 drop-shadow-md" />
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-black leading-none mb-1">{ri.accuracy}%</span>
                      <span className="text-[10px] font-bold text-emerald-100 uppercase tracking-widest">Core Mastey</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* White card holding the RI ring */}
              <div className="bg-white rounded-[2rem] p-6 shadow-2xl flex flex-col items-center shrink-0 w-full max-w-[240px] md:w-auto">
                 <h2 className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-4 text-center">Readiness Tracker</h2>
                 <CircularProgress value={ri.readiness_index} size={150} strokeWidth={14} />
              </div>
            </div>
          </div>
        </motion.div>

        {/* 2. Main Actions */}
        <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
          <Link href="/practice" className="block">
            <div className={cn(premiumCard, "p-8 flex flex-col h-full hover:scale-[1.02] active:scale-[0.98] transition-transform duration-300 group")}>
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-6 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
                <Target className="h-7 w-7" />
              </div>
              <h3 className="text-xl font-extrabold text-gray-900 mb-2">Practice Run</h3>
              <p className="text-gray-500 font-medium text-sm leading-relaxed">Adaptive learning mode adjusting to your strengths and weaknesses.</p>
            </div>
          </Link>
          <Link href="/exam/select" className="block">
            <div className={cn(premiumCard, "p-8 flex flex-col h-full hover:scale-[1.02] active:scale-[0.98] transition-transform duration-300 group")}>
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-6 group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-300">
                <Clock className="h-7 w-7" />
              </div>
              <h3 className="text-xl font-extrabold text-gray-900 mb-2">Take Exam</h3>
              <p className="text-gray-500 font-medium text-sm leading-relaxed">Simulated past papers with strict timing to test your mental endurance.</p>
            </div>
          </Link>
        </motion.div>

        {/* 3. Consistency / Weekly Goals */}
        <motion.div variants={itemVars} className="mb-10">
          <h2 className={sectionHeader}>
            <Flame className="h-6 w-6 text-orange-500" fill="currentColor" />
            Weekly Goals
          </h2>
          <div className={cn(premiumCard, "p-6 md:p-8 flex flex-col sm:flex-row items-center justify-between gap-8")}>
             <div className="text-center sm:text-left">
                <p className="font-extrabold text-gray-900 text-lg mb-1">Daily Log In</p>
                <p className="text-sm font-medium text-gray-500">Keep the momentum going. Longest run: {streak.longest}d</p>
             </div>
             <div className="flex gap-2.5">
                {[...Array(7)].map((_, i) => {
                  const isActive = i < Math.min(streak.current, 7);
                  return (
                    <div 
                      key={i} 
                      className={cn(
                        "w-10 h-10 sm:w-12 sm:h-12 rounded-[14px] flex items-center justify-center shadow-sm transition-all duration-500",
                        isActive ? "bg-orange-50 ring-1 ring-orange-200 text-orange-500 shadow-orange-500/10" : "bg-gray-50 ring-1 ring-black/5 text-gray-300"
                      )}
                    >
                      {isActive && <Flame className="h-5 w-5 sm:h-6 sm:w-6" fill="currentColor" />}
                    </div>
                  )
                })}
             </div>
          </div>
        </motion.div>

        {/* 4. Weak Topics to Level Up */}
        <motion.div variants={itemVars} className="mb-10">
          <h2 className={sectionHeader}>
            <TrendingDown className="h-6 w-6 text-red-500" />
            Areas to Level Up
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {weakTopics.length > 0 ? (
              weakTopics.slice(0, 4).map((t) => (
                <div key={t.topic} className={cn(premiumCard, "p-6 flex flex-col gap-5 hover:ring-red-500/20 transition-shadow")}>
                  <div className="flex items-start justify-between gap-4">
                     <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center shrink-0">
                       <TrendingDown className="h-6 w-6 text-red-500" />
                     </div>
                     <div className="flex-1 min-w-0 pt-1">
                        <h4 className="font-bold text-gray-900 leading-tight mb-2 truncate">{t.topic}</h4>
                        <div className="flex items-center gap-2">
                           <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                             <div className="h-full bg-red-400 rounded-full" style={{ width: `${t.fail_ratio * 100}%` }}/>
                           </div>
                           <p className="text-[10px] font-black text-red-600 uppercase tracking-widest shrink-0">{Math.round(t.fail_ratio * 100)}% Miss</p>
                        </div>
                     </div>
                  </div>
                  <Link href={`/practice?topic=${encodeURIComponent(t.topic)}`} className="w-full">
                     <button className="w-full bg-red-50 hover:bg-red-100 text-red-700 active:scale-[0.98] transition-all font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2">
                       Train Here
                       <ArrowRight className="h-4 w-4" />
                     </button>
                  </Link>
                </div>
              ))
            ) : (
                <div className={cn(premiumCard, "p-10 col-span-full flex flex-col items-center justify-center text-center bg-emerald-50/30")}>
                   <div className="w-16 h-16 rounded-[1.5rem] bg-emerald-100 flex items-center justify-center mb-5 text-emerald-600 shadow-sm">
                     <CheckCircle2 className="h-8 w-8" />
                   </div>
                   <h3 className="text-xl font-extrabold text-gray-900 mb-2">All clear!</h3>
                   <p className="text-gray-500 font-medium">You don't have any significant weak areas yet. Keep playing to collect data.</p>
                </div>
            )}
          </div>
        </motion.div>

        {/* 5. Subscribed Subjects Grid */}
        <motion.div variants={itemVars} className="mb-10">
           <h2 className={sectionHeader}>
            <Compass className="h-6 w-6 text-indigo-500" />
            Your Subjects
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.subjects.map(s => (
              <div 
                key={s.id} 
                onClick={() => setSelectedSubject(s.id)}
                className={cn(
                  premiumCard, 
                  "p-6 flex flex-col justify-between cursor-pointer active:scale-[0.98] transition-all", 
                  s.id === selectedSubject ? "ring-2 ring-indigo-500 bg-indigo-50/20 shadow-indigo-500/10" : "hover:ring-1 hover:ring-gray-300"
                )}
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="font-extrabold text-gray-900 text-lg mb-1">{s.name}</h3>
                    <p className="text-xs font-semibold text-gray-500">{s.level}</p>
                  </div>
                  {s.id === selectedSubject ? (
                     <span className="bg-indigo-100 text-indigo-700 text-[10px] font-black px-3 py-1.5 rounded-xl uppercase tracking-widest">Active Focus</span>
                  ) : (
                     <span className="w-8 h-8 rounded-full border-2 border-gray-100 flex items-center justify-center">
                       <CheckCircle2 className="h-4 w-4 text-transparent" />
                     </span>
                  )}
                </div>
                <div className="flex justify-between items-center text-xs font-bold text-gray-400 w-full group">
                   <span className="group-hover:text-indigo-600 transition-colors">Switch Context</span>
                   <ChevronRight className="h-4 w-4 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* 6. Activity Log List */}
        <motion.div variants={itemVars} className="mb-10">
          <div className="flex items-center justify-between mb-4 px-1">
            <h2 className="text-xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
               <Activity className="h-6 w-6 text-blue-500" />
               Recent Expeditions
            </h2>
            <Link href="/history" className="text-[11px] font-black text-blue-600 hover:text-blue-800 uppercase tracking-widest bg-blue-50 px-3 py-1.5 rounded-lg active:scale-95 transition-transform">
               View All
            </Link>
          </div>
          <div className={cn(premiumCard, "overflow-hidden px-0 py-0 divide-y divide-gray-50")}>
             {data.recent_sessions.length === 0 ? (
                <div className="p-10 text-center bg-gray-50/30">
                  <p className="text-sm text-gray-500 font-medium">No activity logged.</p>
                </div>
             ) : (
                data.recent_sessions.slice(0, 5).map(s => {
                  const isGood = s.percentage != null && s.percentage >= 70;
                  const isBad = s.percentage != null && s.percentage < 40;
                  return (
                    <div key={s.session_id} className="p-6 flex items-center gap-5 hover:bg-gray-50/50 transition-colors group">
                       <div className={cn("w-14 h-14 rounded-[18px] flex items-center justify-center shrink-0", s.mode === 'exam' ? 'bg-indigo-50 text-indigo-500' : 'bg-emerald-50 text-emerald-500')}>
                          {s.mode === "exam" ? <Clock className="h-6 w-6" /> : <Target className="h-6 w-6" />}
                       </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-base font-extrabold text-gray-900 truncate mb-1">
                          {s.subject_name || "Unknown"} P{s.paper_number}
                        </p>
                        <div className="flex items-center gap-2">
                           <span className="text-[11px] font-black uppercase tracking-widest text-gray-400/80">{s.mode} Run</span>
                           <span className="w-1 h-1 bg-gray-300 rounded-full"/>
                           <span className="text-[11px] text-gray-400 font-extrabold tracking-wide">
                             {s.completed_at ? new Date(s.completed_at).toLocaleDateString() : 'N/A'}
                           </span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1.5 shrink-0">
                        {s.percentage != null ? (
                          <span className={cn("text-xl font-black tracking-tight", isGood ? "text-emerald-500" : isBad ? "text-red-500" : "text-amber-500")}>
                             {s.percentage}%
                          </span>
                        ) : (
                          <span className="text-xl font-black text-gray-800 tracking-tight">{s.score}/{s.total_marks}</span>
                        )}
                        <Link href={`/exam/${s.session_id}/results`} className="text-[10px] font-black uppercase tracking-widest text-gray-300 group-hover:text-blue-600 transition-colors flex items-center gap-1">
                          Review <ArrowRight className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  )
                })
             )}
          </div>
        </motion.div>

        {/* 7. Syllabus Coverage Footer */}
        {data.coverage && (
          <motion.div variants={itemVars} className="mb-6 opacity-60 hover:opacity-100 transition-opacity">
            <h2 className="text-sm font-extrabold text-gray-900 tracking-widest uppercase mb-3 px-1 text-center">Syllabus Expansion</h2>
            <div className="bg-transparent border-none p-0">
              {data.coverage.uncovered.length > 0 ? (
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <span className="text-xs font-bold text-gray-500 mr-2">Unknown Territories:</span>
                  {data.coverage.uncovered.slice(0, 6).map(topic => (
                    <span key={topic.topic} className="bg-gray-100 text-gray-600 text-[10px] font-bold px-3 py-1.5 rounded-lg border border-gray-200/50">
                      {topic.topic}
                    </span>
                  ))}
                  {data.coverage.uncovered.length > 6 && (
                    <span className="text-[10px] font-black text-gray-400 ml-1">
                      +{data.coverage.uncovered.length - 6} more
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-sm text-emerald-600 font-bold flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> You've explored the entire syllabus!
                </p>
              )}
            </div>
          </motion.div>
        )}

      </motion.div>
    </div>
  );
}
