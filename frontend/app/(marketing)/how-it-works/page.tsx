"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileText, BarChart3, GraduationCap } from "lucide-react";

export default function HowItWorksPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        {/* Intro */}
        <section className="px-6 pb-20">
          <div className="max-w-4xl mx-auto text-center mb-16">
            <h1 className="text-calm-h1 mb-6 text-foreground">How ZimPrep helps <br className="hidden md:block"/>you prepare properly.</h1>
            <p className="text-calm-body max-w-2xl mx-auto">
              A disciplined, three-step process designed to move you from uncertainty to exam readiness.
            </p>
          </div>
        </section>

        {/* 3-Step Flow */}
        <section className="px-6 pb-24">
          <div className="max-w-5xl mx-auto space-y-24">
            {/* Step 1 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
               <div className="order-2 md:order-1 bg-zinc-50 rounded-[2.5rem] p-8 md:p-12 aspect-[4/3] flex items-center justify-center border border-zinc-100">
                  <div className="text-center space-y-4">
                     <FileText className="w-16 h-16 text-zinc-300 mx-auto" />
                     <p className="font-medium text-zinc-400">Subject Selection Interface</p>
                  </div>
               </div>
               <div className="order-1 md:order-2">
                  <span className="text-primary font-bold tracking-wider text-sm uppercase mb-2 block">Step 01</span>
                  <h2 className="text-3xl md:text-4xl font-semibold mb-4">Select your subject and paper.</h2>
                  <p className="text-muted-foreground text-lg leading-relaxed">
                    Choose from our library of ZIMSEC-aligned subjects. Select specific papers (e.g., Paper 1 or Paper 2) to practice the exact format you will face in the exam room.
                  </p>
               </div>
            </div>

            {/* Step 2 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
               <div className="order-1">
                  <span className="text-primary font-bold tracking-wider text-sm uppercase mb-2 block">Step 02</span>
                  <h2 className="text-3xl md:text-4xl font-semibold mb-4">Practice with examiner logic.</h2>
                  <p className="text-muted-foreground text-lg leading-relaxed">
                    Answer questions under timed conditions. Our system doesn&apos;t just check if you are &quot;right&quot; or &quot;wrong&quot;—it checks if your answer contains the specific keywords and logical steps examiners award marks for.
                  </p>
               </div>
               <div className="order-2 bg-zinc-50 rounded-[2.5rem] p-8 md:p-12 aspect-[4/3] flex items-center justify-center border border-zinc-100">
                  <div className="text-center space-y-4">
                     <GraduationCap className="w-16 h-16 text-zinc-300 mx-auto" />
                     <p className="font-medium text-zinc-400">Examiner Marking View</p>
                  </div>
               </div>
            </div>

            {/* Step 3 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
               <div className="order-2 md:order-1 bg-zinc-50 rounded-[2.5rem] p-8 md:p-12 aspect-[4/3] flex items-center justify-center border border-zinc-100">
                  <div className="text-center space-y-4">
                     <BarChart3 className="w-16 h-16 text-zinc-300 mx-auto" />
                     <p className="font-medium text-zinc-400">Progress Dashboard</p>
                  </div>
               </div>
               <div className="order-1 md:order-2">
                  <span className="text-primary font-bold tracking-wider text-sm uppercase mb-2 block">Step 03</span>
                  <h2 className="text-3xl md:text-4xl font-semibold mb-4">Track and improve.</h2>
                  <p className="text-muted-foreground text-lg leading-relaxed">
                    Review your performance instantly. Identify weak topics, understand where you lost marks, and track your readiness over time.
                  </p>
               </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-24 px-6 bg-zinc-50 border-t border-border/40 text-center">
           <div className="max-w-2xl mx-auto">
              <h2 className="text-3xl font-semibold mb-6">Built to build confidence.</h2>
              <p className="text-muted-foreground mb-8">
                No tricks. Just structured, effective preparation.
              </p>
              <Button size="lg" asChild className="btn-primary h-14 px-12 text-lg rounded-full">
                <Link href="/register">Start Practicing</Link>
              </Button>
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
