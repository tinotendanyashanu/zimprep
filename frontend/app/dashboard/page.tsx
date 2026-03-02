"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Settings, Play, Zap, ArrowRight, Target, Flame } from 'lucide-react';
import { DashboardHeader } from '@/components/dashboard/header';
import { SubjectCard } from '@/components/dashboard/subject-card';
import { LoadingState } from '@/components/system/LoadingState';
import { useDashboard, DashboardData } from '@/lib/use-dashboard';
import { getUser } from '@/lib/auth';

interface UserProfile {
  name: string;
  level: string;
  subjects: string[];
  goal: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { data, loading, error, traceId } = useDashboard();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [userName, setUserName] = useState("Student");

  useEffect(() => {
    // Keep local profile for name/subjects if needed, but rely on pipeline for dynamic data
    const storedProfile = localStorage.getItem("user_profile");
    if (storedProfile) {
      setProfile(JSON.parse(storedProfile));
    }
    const user = getUser();
    if (user?.name) {
        setUserName(user.name.split(' ')[0]); // First name
    }
  }, []);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingState variant="spinner" text="Loading your dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-4 p-6 text-center">
        <div className="p-4 rounded-full bg-red-50 text-red-600 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-alert-circle"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
        </div>
        <h2 className="text-xl font-bold text-zinc-900">Unable to load dashboard</h2>
        <p className="text-zinc-500 max-w-md">{error}</p>
        
        <Button onClick={() => window.location.reload()} variant="outline" className="mt-4">
            Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50/50">
      <DashboardHeader />
      
      <main className="max-w-7xl mx-auto p-4 md:p-8 lg:p-12 space-y-8 md:space-y-12 animate-in fade-in duration-500 delay-100 pb-24">
        
        {/* Welcome & Action Layer */}
        <section className="space-y-6">
            <div className="space-y-2">
                <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900">
                    Hello, {userName}
                </h1>
                <p className="text-zinc-500 text-lg">Ready to make progress today?</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                {/* 1. Continue Last Session (High Priority) */}
                {data?.last_session ? (
                     <div className="group relative overflow-hidden bg-white p-6 rounded-3xl border border-zinc-200 shadow-sm transition-all hover:shadow-md hover:border-primary/20 cursor-pointer"
                          onClick={() => router.push(`/exam/${data.last_session?.exam_id}`)}>
                        <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Play className="w-24 h-24 text-primary" />
                        </div>
                        <div className="relative z-10 flex flex-col items-start gap-4">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-bold uppercase tracking-wider">
                                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                                In Progress
                            </span>
                            <div>
                                <h3 className="text-xl font-bold text-zinc-900 mb-1 line-clamp-1">{data.last_session.exam_name}</h3>
                                <p className="text-zinc-500 text-sm">{data.last_session.subject} • {data.last_session.progress}% complete</p>
                            </div>
                            <Button className="rounded-full pl-6 pr-6 bg-zinc-900 hover:bg-zinc-800 text-white mt-2 group-hover:translate-x-1 transition-transform">
                                Resume Session <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                        </div>
                         {/* Progress Bar overlay at bottom */}
                         <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-100">
                             <div className="h-full bg-primary/80" style={{ width: `${data.last_session.progress}%` }} />
                         </div>
                     </div>
                ) : (
                    // Fallback if no active session: Start a generic quick practice
                     <div className="bg-zinc-900 text-white p-6 rounded-3xl cursor-pointer hover:bg-zinc-800 transition-colors flex flex-col justify-between min-h-[180px]"
                          onClick={() => router.push('/subjects/Mathematics')}> {/* Fallback to Math or generic selector */}
                        <div>
                             <h3 className="text-xl font-bold mb-2">Start a New Session</h3>
                             <p className="text-zinc-400 text-sm">Pick a subject and start practicing focused topics.</p>
                        </div>
                        <div className="flex justify-end">
                            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                                <ArrowRight className="w-5 h-5 text-white" />
                            </div>
                        </div>
                     </div>
                )}

                {/* 2. Daily Challenge */}
                {data?.daily_challenge && (
                    <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500 to-violet-600 p-6 rounded-3xl text-white shadow-lg cursor-pointer transition-transform hover:scale-[1.02]"
                         onClick={() => router.push(`/daily-challenge/${data.daily_challenge?.id}`)}>
                        <div className="absolute top-0 right-0 p-6 opacity-20">
                            <Zap className="w-24 h-24 text-white rotate-12" />
                        </div>
                        <div className="relative z-10 h-full flex flex-col justify-between">
                             <div className="flex items-start justify-between">
                                 <div>
                                     <div className="flex items-center gap-2 mb-2">
                                        <h3 className="text-xl font-bold">Daily Challenge</h3>
                                        <div className="flex items-center gap-1 px-2 py-0.5 bg-white/20 rounded-full text-[10px] font-bold uppercase tracking-wider backdrop-blur-sm">
                                            <Flame className="w-3 h-3 text-orange-400 fill-orange-400" />
                                            Streak: {data.daily_challenge.streak}
                                        </div>
                                     </div>
                                     <p className="text-indigo-100 text-sm font-medium">{data.daily_challenge.title}</p>
                                     <p className="text-indigo-200 text-xs mt-1">{data.daily_challenge.questions_count} Questions • 5 Minutes</p>
                                 </div>
                             </div>
                             <div className="mt-6 flex items-center gap-2 text-sm font-bold text-white/90">
                                <span>Start Challenge</span>
                                <ArrowRight className="w-4 h-4" />
                             </div>
                        </div>
                    </div>
                )}
            </div>
        </section>

        {/* Weak Topics Shortcut (Conditional) */}
        {data?.recommendations && data.recommendations.length > 0 && (
             <section>
                 <div className="flex items-center gap-2 mb-4">
                     <Target className="w-5 h-5 text-rose-500" />
                     <h2 className="text-lg font-bold text-zinc-900">Recommended Focus</h2>
                 </div>
                 <div className="bg-rose-50/50 border border-rose-100 rounded-3xl p-2 md:p-3 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                     {data.recommendations.slice(0, 3).map((rec, i) => (
                         <div key={i} className="bg-white p-4 rounded-2xl border border-rose-100/50 shadow-sm hover:shadow-md hover:border-rose-200 transition-all cursor-pointer"
                              onClick={() => router.push(`/subjects/${encodeURIComponent("Mathematics")}?topic=${encodeURIComponent(rec.topic)}`)}> {/* Naive link, creates intent */}
                             <div className="flex justify-between items-start mb-2">
                                 <h4 className="font-bold text-zinc-900 text-sm line-clamp-1">{rec.topic}</h4>
                                 <span className="text-[10px] font-bold text-rose-600 bg-rose-100 px-2 py-0.5 rounded-full uppercase">Weakness</span>
                             </div>
                             <p className="text-xs text-zinc-500 line-clamp-2 mb-3">{rec.reason}</p>
                             <div className="flex items-center text-xs font-medium text-rose-600">
                                 Practice Topic <ArrowRight className="w-3 h-3 ml-1" />
                             </div>
                         </div>
                     ))}
                 </div>
             </section>
        )}

        {/* Subjects Grid */}
        <section>
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-semibold tracking-tight text-zinc-900">Subjects</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
               {(profile?.subjects || ['Mathematics', 'Physics', 'History', 'Geography', 'Chemistry']).map((subject) => (
                   <SubjectCard key={subject} subject={subject} />
               ))}

               {/* Add Subject Card */}
               <div className="p-6 rounded-3xl border-2 border-dashed border-zinc-200 hover:border-primary/30 hover:bg-primary/5 transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-4 min-h-[160px] md:min-h-[200px] opacity-60 hover:opacity-100 group">
                   <div className="w-12 h-12 rounded-full bg-zinc-100 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                       <span className="text-2xl text-zinc-400 group-hover:text-primary transition-colors">+</span>
                   </div>
                   <p className="font-medium text-zinc-500 group-hover:text-primary transition-colors">Add Subject</p>
               </div>
            </div>
        </section>

      </main>
    </div>
  );
}
