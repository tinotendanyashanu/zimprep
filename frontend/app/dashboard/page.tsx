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
    <div className="min-h-screen bg-zinc-50/50">
      <DashboardHeader />
      
      <main className="max-w-7xl mx-auto p-6 md:p-12 space-y-12 animate-in fade-in duration-500 delay-100">
        
        {/* Welcome Section */}
        <div className="space-y-4">
           <h1 className="text-calm-h2">Overview</h1>
           <p className="text-calm-body text-base max-w-2xl">
              Track your progress and focus on areas that need improvement.
           </p>
        </div>

        {/* AI Recommendations */}
        {data?.recommendations && data.recommendations.length > 0 && (
            <div className="grid gap-6">
                <h3 className="text-calm-h3">Recommended Focus</h3>
                <div className="grid md:grid-cols-2 gap-4">
                    {data.recommendations.map((rec, i) => (
                        <div key={i} className="bg-emerald-50/50 border border-emerald-100 p-6 rounded-2xl transition-all hover:bg-emerald-50">
                            <div className="flex items-start justify-between mb-2">
                                <h4 className="font-bold text-emerald-900">{rec.topic}</h4>
                                <span className="px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-800 text-[10px] font-bold uppercase tracking-wide">
                                    Priority
                                </span>
                            </div>
                            <p className="text-emerald-700 text-sm mb-4">{rec.reason}</p>
                            <div className="flex gap-2">
                                {rec.resources.map((res, j) => (
                                    <span key={j} className="text-xs bg-white text-emerald-600 px-2 py-1 rounded border border-emerald-100">
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
                 <h3 className="text-calm-h3 mb-6">Performance</h3>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-3xl border border-zinc-200 shadow-sm">
                        <p className="text-sm text-zinc-500 uppercase tracking-widest font-semibold mb-2">Average Grade</p>
                        <div className="text-5xl font-serif text-zinc-900">{data.performance.average_grade}</div>
                    </div>
                     <div className="bg-white p-6 rounded-3xl border border-zinc-200 shadow-sm">
                        <p className="text-sm text-zinc-500 uppercase tracking-widest font-semibold mb-2">Trend</p>
                        <div className="flex items-center gap-2">
                            <span className={`text-lg font-medium ${
                                data.performance.improvement_trend === 'up' ? 'text-green-600' : 
                                data.performance.improvement_trend === 'down' ? 'text-red-600' : 'text-zinc-600'
                            }`}>
                                {data.performance.improvement_trend === 'up' ? 'Improving' : 
                                 data.performance.improvement_trend === 'down' ? 'Declining' : 'Stable'}
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
                    <h3 className="text-calm-h3">Recent Activity</h3>
                    <Button variant="outline" size="sm" onClick={() => router.push('/history')}>
                        View All
                    </Button>
                </div>
                <div className="space-y-3">
                    {data.recent_exams.map((exam) => (
                        <div key={exam.exam_id} className="flex items-center justify-between p-4 bg-white border border-zinc-200 rounded-xl hover:border-zinc-300 transition-all cursor-pointer" onClick={() => router.push(`/results/${exam.trace_id || exam.exam_id}`)}>
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white ${
                                    exam.grade === 'A' ? 'bg-zinc-900' : 'bg-zinc-400'
                                }`}>
                                    {exam.grade}
                                </div>
                                <div>
                                    <h4 className="font-semibold text-zinc-900">{exam.exam_name}</h4>
                                    <p className="text-xs text-zinc-500">{new Date(exam.date).toLocaleDateString()}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-sm font-medium text-zinc-900">{exam.marks}/{exam.max_marks}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* Subjects Grid (Legacy/Static for navigation) */}
        <div>
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-calm-h3">Subjects</h3>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
               {(profile?.subjects || ['Mathematics', 'Physics', 'History']).map((subject) => (
                   <SubjectCard key={subject} subject={subject} />
               ))}

               {/* Add Subject Card */}
               <div className="p-6 rounded-3xl border-2 border-dashed border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-4 min-h-[200px] opacity-60 hover:opacity-100">
                   <div className="w-12 h-12 rounded-full bg-zinc-100 flex items-center justify-center">
                       <span className="text-2xl text-zinc-400">+</span>
                   </div>
                   <p className="font-medium text-zinc-500">Add Subject</p>
               </div>
            </div>
        </div>

      </main>
    </div>
  );
}
