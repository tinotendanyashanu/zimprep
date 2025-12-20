"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, TrendingUp, Clock, Target, ArrowRight } from "lucide-react";

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-6 h-6 bg-[#065F46] rounded-lg flex items-center justify-center">
              <span className="text-xs text-white font-bold">Z</span>
            </div>
            <span className="font-bold text-zinc-900">ZimPrep</span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-zinc-600">Tinashe M.</span>
            <div className="w-8 h-8 rounded-full bg-[#065F46] flex items-center justify-center">
              <span className="text-sm text-white font-medium">T</span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Welcome */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-zinc-900 mb-2">Welcome back, Tinashe</h1>
          <p className="text-zinc-600">Continue your exam preparation journey</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-5 h-5 text-[#065F46]" />
                <span className="text-xs text-zinc-500 uppercase">Total Time</span>
              </div>
              <div className="text-3xl font-bold text-zinc-900">24h</div>
              <div className="text-xs text-zinc-500 mt-1">Practice time</div>
            </CardContent>
          </Card>

          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <Target className="w-5 h-5 text-[#065F46]" />
                <span className="text-xs text-zinc-500 uppercase">Completed</span>
              </div>
              <div className="text-3xl font-bold text-zinc-900">12</div>
              <div className="text-xs text-zinc-500 mt-1">Exam papers</div>
            </CardContent>
          </Card>

          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-[#065F46]" />
                <span className="text-xs text-zinc-500 uppercase">Average</span>
              </div>
              <div className="text-3xl font-bold text-zinc-900">78%</div>
              <div className="text-xs text-emerald-600 mt-1">↑ 12% from last week</div>
            </CardContent>
          </Card>

          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <BookOpen className="w-5 h-5 text-[#065F46]" />
                <span className="text-xs text-zinc-500 uppercase">Subjects</span>
              </div>
              <div className="text-3xl font-bold text-zinc-900">5</div>
              <div className="text-xs text-zinc-500 mt-1">Active subjects</div>
            </CardContent>
          </Card>
        </div>

        {/* Subjects Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-zinc-900 mb-6">Your Subjects</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { name: "Mathematics", papers: 2, progress: 65, color: "blue" },
              { name: "Physics", papers: 2, progress: 45, color: "emerald" },
              { name: "Chemistry", papers: 2, progress: 80, color: "purple" },
            ].map((subject) => (
              <Card key={subject.name} className="border-zinc-200 bg-white hover-lift cursor-pointer">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-bold text-zinc-900 text-lg mb-1">{subject.name}</h3>
                      <p className="text-sm text-zinc-500">{subject.papers} papers available</p>
                    </div>
                    <div className="w-12 h-12 rounded-lg bg-[#065F46]/10 flex items-center justify-center">
                      <BookOpen className="w-6 h-6 text-[#065F46]" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-600">Progress</span>
                      <span className="font-medium text-zinc-900">{subject.progress}%</span>
                    </div>
                    <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#065F46] rounded-full"
                        style={{ width: `${subject.progress}%` }}
                      />
                    </div>
                  </div>
                  <Button asChild className="w-full mt-4 bg-[#065F46] hover:bg-[#055444]">
                    <Link href={`/exam/${subject.name.toLowerCase()}`}>
                      Start Practice
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 mb-6">Recent Activity</h2>
          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="space-y-4">
                {[
                  { subject: "Mathematics P2", score: 82, date: "2 hours ago" },
                  { subject: "Physics P1", score: 76, date: "Yesterday" },
                  { subject: "Chemistry P2", score: 91, date: "2 days ago" },
                ].map((activity, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-3 border-b border-zinc-100 last:border-0"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-[#065F46]/10 flex items-center justify-center">
                        <BookOpen className="w-5 h-5 text-[#065F46]" />
                      </div>
                      <div>
                        <div className="font-medium text-zinc-900">{activity.subject}</div>
                        <div className="text-sm text-zinc-500">{activity.date}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-[#065F46]">{activity.score}%</div>
                      <div className="text-xs text-zinc-500">Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
