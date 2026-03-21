"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';
import { DashboardHeader } from '@/components/dashboard/header';
import { SubjectCard } from '@/components/dashboard/subject-card';
import { LoadingState } from '@/components/system/LoadingState';
import { useDashboard, DashboardData } from '@/lib/use-dashboard';

interface UserProfile {
  level: string;
  subjects: string[];
  goal: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { data, loading, error } = useDashboard();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    // Keep local profile for name/subjects if needed, but rely on pipeline for dynamic data
    const storedProfile = localStorage.getItem("user_profile");
    if (storedProfile) {
      setProfile(JSON.parse(storedProfile));
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
    <div className="min-h-screen bg-background">
      <DashboardHeader title="ZimPrep" />
      
      <main className="max-w-7xl mx-auto p-6 md:p-12 space-y-12 animate-in fade-in duration-500 delay-100">
        
        {/* Welcome Section */}
        <div className="space-y-2">
           <h1 className="text-4xl md:text-5xl font-black tracking-tight text-foreground">Overview</h1>
           <p className="text-lg text-muted-foreground font-medium max-w-2xl">
              Track your progress and focus on areas that need improvement.
           </p>
        </div>

        {/* AI Recommendations */}
        {data?.recommendations && data.recommendations.length > 0 && (
            <div className="grid gap-6">
                <h3 className="text-calm-h3">Recommended Focus</h3>
                <div className="grid md:grid-cols-2 gap-4">
                    {data.recommendations.map((rec, i) => (
                        <div key={i} className="bg-emerald-100 border-2 border-emerald-300 p-6 rounded-2xl transition-all hover:bg-emerald-200 hover:shadow-gamified cursor-pointer shadow-sm">
                            <div className="flex items-start justify-between mb-3">
                                <h4 className="font-extrabold text-emerald-900 text-lg">{rec.topic}</h4>
                                <span className="px-3 py-1 rounded-xl bg-orange-400 text-white text-[10px] font-black uppercase tracking-widest shadow-sm">
                                    Priority
                                </span>
                            </div>
                            <p className="text-emerald-800 text-sm mb-5 font-medium">{rec.reason}</p>
                            <div className="flex gap-2 flex-wrap">
                                {rec.resources.map((res, j) => (
                                    <span key={j} className="text-xs font-bold bg-white text-emerald-700 px-3 py-1.5 rounded-xl border-2 border-emerald-200 shadow-sm">
                                        {res}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* Performance Overview */}
        {data?.performance && (
            <div>
                 <h3 className="text-2xl font-black text-foreground mb-6 flex items-center gap-2"><div className="w-3 h-8 bg-blue-500 rounded-full"></div> Performance</h3>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-card p-6 rounded-2xl border-2 border-border shadow-gamified hover:shadow-gamified-lg transition-all">
                        <p className="text-xs text-muted-foreground uppercase tracking-widest font-black mb-3">Average Grade</p>
                        <div className="text-6xl font-black text-primary drop-shadow-sm">{data.performance.average_grade}</div>
                    </div>
                     <div className="bg-card p-6 rounded-2xl border-2 border-border shadow-gamified hover:shadow-gamified-lg transition-all">
                        <p className="text-xs text-muted-foreground uppercase tracking-widest font-black mb-3">Trend</p>
                        <div className="flex items-center gap-2">
                            <span className={`text-2xl font-black ${
                                data.performance.improvement_trend === 'up' ? 'text-accent' : 
                                data.performance.improvement_trend === 'down' ? 'text-destructive' : 'text-zinc-400'
                            }`}>
                                {data.performance.improvement_trend === 'up' ? '↗ Improving' : 
                                 data.performance.improvement_trend === 'down' ? '↘ Declining' : '→ Stable'}
                            </span>
                        </div>
                    </div>
                 </div>
            </div>
        )}

        {/* Recent Exams */}
        {data?.recent_exams && data.recent_exams.length > 0 && (
            <div>
                 <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-black text-foreground flex items-center gap-2"><div className="w-3 h-8 bg-orange-400 rounded-full"></div> Recent Activity</h3>
                    <Button variant="outline" size="sm" onClick={() => router.push('/history')}>
                        View All
                    </Button>
                </div>
                <div className="space-y-4">
                    {data.recent_exams.map((exam) => (
                        <div key={exam.exam_id} className="flex items-center justify-between p-5 bg-card border-2 border-border shadow-sm rounded-2xl hover:shadow-gamified transition-all cursor-pointer hover:-translate-y-1 active:translate-y-0 active:shadow-sm" onClick={() => router.push(`/results/${exam.exam_id}`)}>
                            <div className="flex items-center gap-5">
                                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-2xl text-white shadow-sm border-2 border-black/10 ${
                                    ['A', 'A*', 'B'].includes(exam.grade) ? 'bg-accent' : ['C', 'D'].includes(exam.grade) ? 'bg-amber-400' : 'bg-destructive'
                                }`}>
                                    {exam.grade}
                                </div>
                                <div>
                                    <h4 className="font-extrabold text-foreground text-lg">{exam.exam_name}</h4>
                                    <p className="text-sm font-medium text-muted-foreground">{new Date(exam.date).toLocaleDateString()}</p>
                                </div>
                            </div>
                            <div className="text-right bg-secondary/50 px-4 py-2 rounded-xl border-2 border-border/50">
                                <span className="text-base font-black text-foreground">{exam.marks} <span className="text-muted-foreground text-sm font-bold">/ {exam.max_marks}</span></span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* Subjects Grid (Legacy/Static for navigation) */}
        <div>
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-black text-foreground flex items-center gap-2"><div className="w-3 h-8 bg-purple-500 rounded-full"></div> Subjects</h3>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
               {(profile?.subjects || ['Mathematics', 'Physics', 'History']).map((subject) => (
                   <SubjectCard key={subject} subject={subject} />
               ))}

               {/* Add Subject Card */}
               <div className="p-6 rounded-3xl border-4 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-4 min-h-[220px] group">
                   <div className="w-16 h-16 rounded-2xl bg-secondary group-hover:bg-primary/20 flex items-center justify-center transition-colors">
                       <span className="text-4xl text-muted-foreground group-hover:text-primary font-black">+</span>
                   </div>
                   <p className="font-bold text-muted-foreground group-hover:text-primary transition-colors uppercase tracking-wide">Add Subject</p>
               </div>
            </div>
        </div>

      </main>
    </div>
  );
}
