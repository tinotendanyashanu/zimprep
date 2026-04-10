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

import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";

// ── Shared Styling constants ──
const premiumCard = "glass-card";
const cardPadding = "p-8";
const sectionHeader = "text-2xl font-bold text-foreground tracking-tight mb-6 flex items-center gap-3 px-1";

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
          stroke="currentColor"
          className="text-muted/30"
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
          className="transition-all duration-1000 ease-out drop-shadow-[0_0_8px_rgba(0,0,0,0.1)]"
        />
      </svg>
      {/* Center Label */}
      <div className="flex flex-col items-center">
        <span className="text-5xl font-bold tracking-tighter text-foreground leading-none">
          {value}
        </span>
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground mt-2">Readiness</span>
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
      <div className="min-h-screen bg-background p-4 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-sm font-medium text-muted-foreground animate-pulse">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <GlassCard className="bg-red-500/10 border-red-500/20 max-w-md w-full p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-foreground mb-2">Something went wrong</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>Try Again</Button>
        </GlassCard>
      </div>
    );
  }

  const containerVars = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  } as const;
  const itemVars = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  } as const;

  // Empty Data Flow (New Student)
  if (!data?.has_data) {
    return (
      <motion.div variants={containerVars} initial="hidden" animate="show" className="min-h-screen bg-background mx-auto max-w-2xl px-6 py-20 flex flex-col items-center justify-center text-center">
        <motion.div variants={itemVars} className="mb-12">
          <div className="w-24 h-24 bg-primary/10 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 shadow-xl shadow-primary/5">
             <Compass className="h-12 w-12 text-primary" />
          </div>
          <h1 className="text-5xl font-bold text-foreground tracking-tight mb-4">Welcome, {name}</h1>
          <p className="text-muted-foreground text-lg leading-relaxed max-w-md mx-auto">Your learning journey begins here. Complete your first session to unlock your readiness insights.</p>
        </motion.div>
        
        <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full">
          <Link href="/practice" className="block">
             <GlassCard className="p-10 flex flex-col items-center gap-4 hover:bg-primary/5 transition-colors group">
              <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                 <Target className="h-8 w-8" />
              </div>
              <div>
                <p className="font-bold text-foreground text-xl">Start Practice</p>
                <p className="text-sm text-muted-foreground mt-1">Adaptive learning mode</p>
              </div>
            </GlassCard>
          </Link>
          <Link href="/exam/select" className="block">
             <GlassCard className="p-10 flex flex-col items-center gap-4 hover:bg-indigo-500/5 transition-colors group">
              <div className="w-16 h-16 bg-indigo-500/10 text-indigo-500 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Clock className="h-8 w-8" />
              </div>
              <div>
                <p className="font-bold text-foreground text-xl">Take Exam</p>
                <p className="text-sm text-muted-foreground mt-1">Timed past papers</p>
              </div>
            </GlassCard>
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
    <div className="min-h-screen bg-background text-foreground pb-28 font-sans">
      <motion.div 
        variants={containerVars} 
        initial="hidden" 
        animate="show" 
        className="mx-auto max-w-5xl px-6 pt-12"
      >
        {/* Top Header Row / Navigation */}
        <motion.div variants={itemVars} className="flex items-center justify-between mb-12">
          <div className="flex flex-col">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
            <p className="text-sm text-muted-foreground font-medium mt-1">Welcome back, {name}</p>
          </div>

          <div className="flex items-center gap-3">
            {data.subjects.length > 1 && (
              <div className="relative group">
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="appearance-none bg-white/50 dark:bg-black/20 backdrop-blur-md ring-1 ring-black/5 dark:ring-white/5 rounded-2xl pl-5 pr-10 py-2.5 text-sm font-bold text-foreground outline-none cursor-pointer shadow-sm hover:ring-primary/20 transition-all"
                >
                  {data.subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground group-hover:text-primary transition-colors">
                   <ChevronRight className="h-4 w-4 rotate-90" />
                </div>
              </div>
            )}
            <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 text-primary">
              <Activity className="w-5 h-5" />
            </div>
          </div>
        </motion.div>

        <AnimatePresence>
          {(subscription?.status === "past_due" || quota?.limit !== null) && (
            <motion.div layout variants={itemVars} className="mb-10 space-y-4">
              {subscription && subscription.status === "past_due" && <PastDueBanner subscription={subscription} />}
              {quota && quota.limit !== null && <QuotaBar quota={quota} />}
            </motion.div>
          )}
        </AnimatePresence>

        {/* 1. Master Hero Section */}
        <motion.div variants={itemVars} className="mb-12">
          <div className="relative group overflow-hidden rounded-[3rem] p-1 shadow-2xl shadow-primary/10">
            {/* Animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary via-emerald-600 to-teal-700 opacity-90 transition-transform duration-700 group-hover:scale-105" />
            
            <div className="relative z-10 bg-black/10 backdrop-blur-sm p-8 md:p-12 rounded-[2.9rem] flex flex-col md:flex-row justify-between items-center gap-12 text-white">
              {/* Soft background aesthetic blurs */}
              <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-[100px] pointer-events-none animate-pulse" />
              <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-emerald-400/20 rounded-full blur-[80px] pointer-events-none" />
              
              <div className="flex-1 text-center md:text-left space-y-8">
                <div>
                  <span className="inline-flex items-center px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-xl text-white text-[11px] font-bold uppercase tracking-[0.2em] mb-8 border border-white/10 shadow-lg">
                    Current Performance
                  </span>
                  <h2 className="text-4xl md:text-6xl font-bold tracking-tight mb-4 leading-[1.1]">
                    {ri.readiness_index >= 75 ? "Scholar Mastery" : ri.readiness_index >= 50 ? "Rising Star" : "Potential Unlocked"}
                  </h2>
                  <p className="text-emerald-50/80 text-lg md:text-xl font-medium max-w-md mx-auto md:mx-0 leading-relaxed">
                    {getRITagline(ri.readiness_index, currentSubjectName)}
                  </p>
                </div>
                
                {/* Stats Pills row */}
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-4">
                  <div className="bg-white/10 backdrop-blur-xl px-6 py-4 rounded-[1.5rem] flex items-center gap-4 border border-white/20 shadow-xl group/stat hover:bg-white/20 transition-all">
                    <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center text-orange-400">
                      <Flame className="h-6 w-6" fill="currentColor" />
                    </div>
                    <div className="flex flex-col text-left">
                      <span className="text-xl font-bold leading-none mb-1">{streak.current} Days</span>
                      <span className="text-[10px] font-bold text-emerald-100 uppercase tracking-widest opacity-70">Active Streak</span>
                    </div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-xl px-6 py-4 rounded-[1.5rem] flex items-center gap-4 border border-white/20 shadow-xl group/stat hover:bg-white/20 transition-all">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                      <Award className="h-6 w-6" />
                    </div>
                    <div className="flex flex-col text-left">
                      <span className="text-xl font-bold leading-none mb-1">{ri.accuracy}%</span>
                      <span className="text-[10px] font-bold text-emerald-100 uppercase tracking-widest opacity-70">Accuracy</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* White card holding the RI ring */}
              <div className="bg-white/95 dark:bg-black/80 backdrop-blur-2xl rounded-[2.5rem] p-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.3)] flex flex-col items-center shrink-0 w-full max-w-[280px] border border-white/20">
                 <h2 className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-8 text-center">Mastery Score</h2>
                 <CircularProgress value={ri.readiness_index} size={180} strokeWidth={16} />
                 <div className="mt-8 pt-8 border-t border-muted/20 w-full text-center">
                    <p className="text-sm font-bold text-foreground">Next Milestone</p>
                    <p className="text-xs text-muted-foreground mt-1">Level 4: Scholar Elite</p>
                 </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 2. Main Actions */}
        <motion.div variants={itemVars} className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-16">
          <Link href="/practice" className="block group">
            <GlassCard className="p-10 flex flex-col h-full hover:bg-primary/5 transition-all duration-500 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <Target className="w-32 h-32 rotate-12" />
              </div>
              <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-8 group-hover:bg-primary group-hover:text-white transition-all duration-500 shadow-lg shadow-primary/10">
                <Target className="h-8 w-8" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-3">Adaptive Practice</h3>
              <p className="text-muted-foreground font-medium text-base leading-relaxed mb-8">AI-driven sessions that evolve with your learning pace and subject mastery.</p>
              <div className="mt-auto flex items-center text-primary font-bold gap-2 group-hover:translate-x-1 transition-transform">
                Start Session <ArrowRight className="h-5 w-5" />
              </div>
            </GlassCard>
          </Link>
          <Link href="/exam/select" className="block group">
            <GlassCard className="p-10 flex flex-col h-full hover:bg-indigo-500/5 transition-all duration-500 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <Clock className="w-32 h-32 -rotate-12" />
              </div>
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center mb-8 group-hover:bg-indigo-500 group-hover:text-white transition-all duration-500 shadow-lg shadow-indigo-500/10">
                <Clock className="h-8 w-8" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-3">Exam Simulation</h3>
              <p className="text-muted-foreground font-medium text-base leading-relaxed mb-8">Full-length past papers under timed conditions to build your confidence.</p>
              <div className="mt-auto flex items-center text-indigo-500 font-bold gap-2 group-hover:translate-x-1 transition-transform">
                Browse Papers <ArrowRight className="h-5 w-5" />
              </div>
            </GlassCard>
          </Link>
        </motion.div>

        {/* 3. Consistency / Weekly Goals */}
        <motion.div variants={itemVars} className="mb-16">
          <h2 className={sectionHeader}>
            <Flame className="h-7 w-7 text-orange-500" fill="currentColor" />
            Learning Momentum
          </h2>
          <GlassCard className="p-8 flex flex-col lg:flex-row items-center justify-between gap-12">
             <div className="text-center lg:text-left">
                <p className="font-bold text-foreground text-2xl mb-2">Weekly Activity</p>
                <p className="text-base font-medium text-muted-foreground">Keep your streak alive to boost retention. Personal best: {streak.longest} days.</p>
             </div>
             <div className="flex gap-3 sm:gap-4 flex-wrap justify-center">
                {[...Array(7)].map((_, i) => {
                  const isActive = i < Math.min(streak.current, 7);
                  return (
                    <motion.div 
                      key={i} 
                      whileHover={{ scale: 1.1 }}
                      className={cn(
                        "w-12 h-12 sm:w-16 sm:h-16 rounded-[1.25rem] flex flex-col items-center justify-center gap-1 shadow-sm transition-all duration-500 border",
                        isActive 
                          ? "bg-orange-500/10 border-orange-500/20 text-orange-500 shadow-orange-500/10" 
                          : "bg-muted/30 border-muted/10 text-muted-foreground opacity-50"
                      )}
                    >
                      <span className="text-[10px] font-bold uppercase tracking-widest">{['M', 'T', 'W', 'T', 'F', 'S', 'S'][i]}</span>
                      {isActive ? <Flame className="h-5 w-5 sm:h-6 sm:w-6" fill="currentColor" /> : <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/30" />}
                    </motion.div>
                  )
                })}
             </div>
          </GlassCard>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
          {/* 4. Weak Topics to Level Up */}
          <motion.div variants={itemVars} className="lg:col-span-2">
            <h2 className={sectionHeader}>
              <TrendingDown className="h-7 w-7 text-red-500" />
              Focus Areas
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {weakTopics.length > 0 ? (
                weakTopics.slice(0, 4).map((t) => (
                  <GlassCard key={t.topic} className="p-8 flex flex-col gap-6 group hover:border-red-500/20 transition-all">
                    <div className="flex items-start justify-between gap-4">
                       <div className="w-14 h-14 rounded-2xl bg-red-500/10 flex items-center justify-center shrink-0 text-red-500 group-hover:scale-110 transition-transform">
                         <TrendingDown className="h-7 w-7" />
                       </div>
                       <div className="flex-1 min-w-0 pt-1">
                          <h4 className="font-bold text-foreground leading-tight mb-3 truncate text-lg">{t.topic}</h4>
                          <div className="flex items-center gap-3">
                             <div className="flex-1 h-2 bg-muted/20 rounded-full overflow-hidden">
                               <motion.div 
                                 initial={{ width: 0 }}
                                 whileInView={{ width: `${t.fail_ratio * 100}%` }}
                                 className="h-full bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.4)]" 
                               />
                             </div>
                             <p className="text-[11px] font-bold text-red-500 uppercase tracking-widest shrink-0">{Math.round(t.fail_ratio * 100)}% Miss</p>
                          </div>
                       </div>
                    </div>
                    <Link href={`/practice?topic=${encodeURIComponent(t.topic)}`} className="w-full">
                       <Button variant="glass" className="w-full text-red-500 hover:bg-red-500/10 border-red-500/20 font-bold py-4 rounded-2xl">
                         Master Topic
                         <ArrowRight className="h-4 w-4 ml-2" />
                       </Button>
                    </Link>
                  </GlassCard>
                ))
              ) : (
                  <GlassCard className="p-12 col-span-full flex flex-col items-center justify-center text-center bg-emerald-500/5 border-emerald-500/10">
                     <div className="w-20 h-20 rounded-[2rem] bg-emerald-500/10 flex items-center justify-center mb-6 text-emerald-500 shadow-xl shadow-emerald-500/10">
                       <CheckCircle2 className="h-10 w-10" />
                     </div>
                     <h3 className="text-2xl font-bold text-foreground mb-2">Subject Mastery Clear</h3>
                     <p className="text-muted-foreground font-medium text-lg">You've maintained high accuracy across all topics. Excellent work!</p>
                  </GlassCard>
              )}
            </div>
          </motion.div>

          {/* 5. Subscribed Subjects Grid */}
          <motion.div variants={itemVars}>
             <h2 className={sectionHeader}>
              <Compass className="h-7 w-7 text-primary" />
              Subjects
            </h2>
            <div className="space-y-4">
              {data.subjects.map(s => (
                <GlassCard 
                  key={s.id} 
                  onClick={() => setSelectedSubject(s.id)}
                  className={cn(
                    "p-6 flex flex-col justify-between cursor-pointer active:scale-95 transition-all group", 
                    s.id === selectedSubject ? "border-primary bg-primary/5 shadow-xl shadow-primary/5" : "hover:border-primary/20"
                  )}
                >
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h3 className="font-bold text-foreground text-xl mb-1 group-hover:text-primary transition-colors">{s.name}</h3>
                      <p className="text-xs font-bold text-muted-foreground uppercase tracking-[0.15em]">{s.level}</p>
                    </div>
                    {s.id === selectedSubject && (
                       <span className="bg-primary text-white text-[10px] font-bold px-3 py-1.5 rounded-full uppercase tracking-widest shadow-lg shadow-primary/20 animate-pulse">Active</span>
                    )}
                  </div>
                  <div className="flex justify-between items-center text-xs font-bold text-muted-foreground w-full">
                     <span className="group-hover:text-primary transition-colors">Select Context</span>
                     <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-all group-hover:text-primary" />
                  </div>
                </GlassCard>
              ))}
            </div>
          </motion.div>
        </div>

        {/* 6. Activity Log List */}
        <motion.div variants={itemVars} className="mb-16">
          <div className="flex items-center justify-between mb-8 px-1">
            <h2 className="text-2xl font-bold text-foreground tracking-tight flex items-center gap-3">
               <Activity className="h-7 w-7 text-primary" />
               Recent Sessions
            </h2>
            <Link href="/history">
               <Button variant="glass" size="sm" className="font-bold tracking-widest uppercase text-[10px]">
                 History
               </Button>
            </Link>
          </div>
          <GlassCard className="overflow-hidden p-0 divide-y divide-muted/10">
             {data.recent_sessions.length === 0 ? (
                <div className="p-16 text-center bg-muted/5">
                  <p className="text-lg text-muted-foreground font-medium">No sessions logged yet. Your journey starts with a single question.</p>
                </div>
             ) : (
                data.recent_sessions.slice(0, 5).map(s => {
                  const isGood = s.percentage != null && s.percentage >= 70;
                  const isBad = s.percentage != null && s.percentage < 40;
                  return (
                    <div key={s.session_id} className="p-8 flex items-center gap-8 hover:bg-white/40 dark:hover:bg-black/20 transition-all group">
                       <div className={cn("w-16 h-16 rounded-[1.5rem] flex items-center justify-center shrink-0 shadow-lg transition-transform group-hover:scale-110", s.mode === 'exam' ? 'bg-indigo-500/10 text-indigo-500 shadow-indigo-500/5' : 'bg-primary/10 text-primary shadow-primary/5')}>
                          {s.mode === "exam" ? <Clock className="h-8 w-8" /> : <Target className="h-8 w-8" />}
                       </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xl font-bold text-foreground truncate mb-2 group-hover:text-primary transition-colors">
                          {s.subject_name || "Unknown"} P{s.paper_number}
                        </p>
                        <div className="flex items-center gap-3">
                           <span className={cn("text-[11px] font-bold uppercase tracking-[0.2em] px-2.5 py-1 rounded-full border", s.mode === 'exam' ? 'text-indigo-500 border-indigo-500/20' : 'text-primary border-primary/20')}>
                            {s.mode}
                           </span>
                           <span className="w-1.5 h-1.5 bg-muted/20 rounded-full"/>
                           <span className="text-xs text-muted-foreground font-bold">
                             {s.completed_at ? new Date(s.completed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A'}
                           </span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        {s.percentage != null ? (
                          <div className={cn("text-3xl font-bold tracking-tighter", isGood ? "text-primary" : isBad ? "text-red-500" : "text-orange-500")}>
                             {s.percentage}<span className="text-lg ml-0.5 opacity-60">%</span>
                          </div>
                        ) : (
                          <div className="text-3xl font-bold text-foreground tracking-tighter">{s.score}<span className="text-lg opacity-40 ml-1">/{s.total_marks}</span></div>
                        )}
                        <Link href={`/exam/${s.session_id}/results`} className="flex items-center gap-2 group/review">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground group-hover/review:text-primary transition-colors">Performance Review</span>
                          <ArrowRight className="h-4 w-4 text-muted-foreground group-hover/review:text-primary transition-transform group-hover/review:translate-x-1" />
                        </Link>
                      </div>
                    </div>
                  )
                })
             )}
          </GlassCard>
        </motion.div>

        {/* 7. Syllabus Coverage Footer */}
        {data.coverage && (
          <motion.div variants={itemVars} className="mb-12">
            <h2 className="text-sm font-bold text-muted-foreground tracking-[0.3em] uppercase mb-6 px-1 text-center opacity-60">Syllabus Expansion</h2>
            <div className="flex flex-wrap items-center justify-center gap-3">
              {data.coverage.uncovered.length > 0 ? (
                <>
                  {data.coverage.uncovered.slice(0, 8).map(topic => (
                    <span key={topic.topic} className="glass text-muted-foreground text-[11px] font-bold px-4 py-2 rounded-full border border-muted/10 hover:border-primary/20 hover:text-primary transition-all cursor-default">
                      {topic.topic}
                    </span>
                  ))}
                  {data.coverage.uncovered.length > 8 && (
                    <span className="text-xs font-bold text-muted-foreground/40 ml-2">
                      + {data.coverage.uncovered.length - 8} more
                    </span>
                  )}
                </>
              ) : (
                <div className="flex items-center gap-3 text-primary font-bold">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                  <span>You've explored the entire syllabus!</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

      </motion.div>
    </div>
  );
}
