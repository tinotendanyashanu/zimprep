"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Info, BarChart, Clock } from "lucide-react";

export default function ParentsPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-20">
          <div className="max-w-4xl mx-auto text-center mb-20">
            <h1 className="text-calm-h1 mb-6 text-foreground">A guide for parents.</h1>
            <p className="text-calm-body max-w-2xl mx-auto">
              How ZimPrep supports your child’s discipline, consistency, and exam readiness.
            </p>
          </div>

          <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-8 mb-20">
             <div className="bg-zinc-50 border border-zinc-100 p-8 rounded-2xl">
                <Clock className="w-10 h-10 text-primary mb-4" />
                <h3 className="text-lg font-bold mb-2">Disciplined Study</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                   ZimPrep discourages random browsing. It focuses on timed, full-paper practice to build mental stamina for the real exam duration.
                </p>
             </div>
             <div className="bg-zinc-50 border border-zinc-100 p-8 rounded-2xl">
                <BarChart className="w-10 h-10 text-primary mb-4" />
                <h3 className="text-lg font-bold mb-2">Transparent Progress</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                   You are not left in the dark. Our marking system gives you and your child a clear, objective view of their current grade level.
                </p>
             </div>
             <div className="bg-zinc-50 border border-zinc-100 p-8 rounded-2xl">
                <Info className="w-10 h-10 text-primary mb-4" />
                <h3 className="text-lg font-bold mb-2">Exam Year Focus</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  While useful for foundation years, ZimPrep is most effective for students in their final examination years: Grade 7, Form 4, and Form 6.
                </p>
             </div>
          </div>

          <div className="max-w-3xl mx-auto bg-zinc-900 text-white rounded-3xl p-8 md:p-12 text-center">
             <h2 className="text-2xl font-bold mb-4">Give them the best chance.</h2>
             <p className="text-zinc-400 mb-8 max-w-xl mx-auto">
                Subscriptions are simple, affordable, and can be cancelled at any time once exams are over.
             </p>
             <div className="flex justify-center gap-4">
                <Button size="lg" className="rounded-full bg-white text-zinc-900 hover:bg-zinc-100 font-bold px-8">
                   View Pricing for Parents
                </Button>
             </div>
          </div>
        </section>
      </main>

      <footer className="py-12 px-6 border-t border-border mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
           <div className="flex flex-col md:flex-row items-center gap-8">
              <Link href="/" className="text-lg font-bold tracking-tight text-foreground">ZimPrep</Link>
              <nav className="flex gap-6 text-sm font-medium text-muted-foreground">
                 <Link href="#" className="hover:text-foreground">Privacy</Link>
                 <Link href="#" className="hover:text-foreground">Terms</Link>
                 <Link href="#" className="hover:text-foreground">Twitter</Link>
              </nav>
           </div>
           <p className="text-sm text-muted-foreground w-full md:w-auto text-center md:text-right">
              &copy; 2025 ZimPrep Inc.
           </p>
        </div>
      </footer>
    </div>
  );
}
