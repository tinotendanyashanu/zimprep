"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DemoPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1 flex flex-col items-center justify-center px-6">
        <div className="max-w-2xl w-full text-center space-y-8">
           <h1 className="text-calm-h2">Experience ZimPrep</h1>
           <p className="text-calm-body max-w-lg mx-auto">
             Try a short, interactive 5-minute practice session to see how our examiner marking engine works.
           </p>
           
           <div className="bg-card border border-border rounded-3xl p-8 md:p-12 shadow-xl my-12">
               {/* Placeholder for actual interactive demo component */}
               <div className="aspect-video bg-zinc-100 rounded-xl flex items-center justify-center mb-8 border border-zinc-200">
                  <p className="text-zinc-400 font-medium">Interactive Demo Module Loading...</p>
               </div>
               
               <div className="flex flex-col gap-4">
                  <Button size="lg" className="w-full btn-primary h-14 text-lg rounded-full">
                     Start 5-Minute Demo
                  </Button>
                  <p className="text-xs text-muted-foreground">No sign-up required for demo.</p>
               </div>
           </div>
           
           <div>
               <Link href="/pricing" className="text-primary font-bold hover:underline">
                  Ready to start for real? View plans.
               </Link>
           </div>
        </div>
      </main>

      <footer className="py-12 px-6 border-t border-border mt-auto w-full">
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
