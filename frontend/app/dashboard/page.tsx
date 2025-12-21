"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';
import { DashboardHeader } from '@/components/dashboard/header';
import { SubjectCard } from '@/components/dashboard/subject-card';
import { LoadingState } from '@/components/system/LoadingState';

interface UserProfile {
  level: string;
  subjects: string[];
  goal: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Auth Guard
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    // 2. Onboarding Guard
    const onboardingCompleted = localStorage.getItem("onboarding_completed");
    if (!onboardingCompleted) {
      router.replace("/onboarding");
      return;
    }

    // 3. Load Profile
    const storedProfile = localStorage.getItem("user_profile");
    if (storedProfile) {
      setProfile(JSON.parse(storedProfile));
    }
    setLoading(false);
  }, [router]);

  if (loading) return <div className="h-screen flex items-center justify-center"><LoadingState variant="spinner" text="Loading workspace..." /></div>;

  return (
    <div className="min-h-screen bg-zinc-50/50">
      <DashboardHeader />
      
      <main className="max-w-7xl mx-auto p-6 md:p-12 space-y-12 animate-in fade-in duration-500 delay-100">
        
        {/* Welcome Section */}
        <div className="space-y-4">
           <h1 className="text-calm-h2">Welcome back.</h1>
           <p className="text-calm-body text-base max-w-2xl">
              You are preparing for <span className="font-semibold text-foreground">{profile?.level === 'O_LEVEL' ? 'O-Levels' : 'A-Levels'}</span>. 
              Focus on one subject at a time to build confidence.
           </p>
        </div>

        {/* Suggested Action */}
        <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-2xl flex items-center justify-between transition-colors hover:bg-emerald-100/50 cursor-pointer" onClick={() => router.push('/recommendations')}>
            <div>
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-bold text-emerald-900">AI Recommendations</h4>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-800 text-[10px] font-bold uppercase tracking-wide">New</span>
                </div>
                <p className="text-emerald-700 text-sm">View evidence-based study suggestions personalized for you.</p>
            </div>
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-200">
                View Suggestions
            </Button>
        </div>

        {/* Subjects Grid */}
        <div>
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-calm-h3">Your Subjects</h3>
                <Button variant="outline" size="sm" className="gap-2">
                    <Settings className="w-4 h-4" /> Manage
                </Button>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
               {(profile?.subjects || []).map((subject) => (
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
