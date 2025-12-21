"use client";

import Link from "next/link";
import { Shield, Fingerprint, Lock } from "lucide-react";

export default function TrustPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-20">
          <div className="max-w-3xl mx-auto text-center mb-20">
             <h1 className="text-calm-h2 mb-6">Trust & Standards</h1>
             <p className="text-calm-body">
                Our commitment to academic integrity and data privacy.
             </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-16">
             {/* 1. Alignment */}
             <div className="flex flex-col md:flex-row gap-8 items-start">
                <div className="bg-zinc-100 p-4 rounded-xl shrink-0">
                    <Shield className="w-8 h-8 text-zinc-900" />
                </div>
                <div>
                    <h3 className="text-xl font-bold mb-3">Academic Alignment</h3>
                    <p className="text-muted-foreground leading-relaxed mb-4">
                        ZimPrep is built specifically for the ZIMSEC curriculum. We audit our question banks regularly to ensure they reflect current syllabus requirements and examination standards. We are not an official partner of ZIMSEC, but we adhere strictly to their published public standards for examination quality.
                    </p>
                </div>
             </div>

             {/* 2. Marking */}
             <div className="flex flex-col md:flex-row gap-8 items-start">
                <div className="bg-zinc-100 p-4 rounded-xl shrink-0">
                    <Fingerprint className="w-8 h-8 text-zinc-900" />
                </div>
                <div>
                    <h3 className="text-xl font-bold mb-3">Marking Philosophy</h3>
                    <p className="text-muted-foreground leading-relaxed mb-4">
                        Our marking algorithms are designed to mimic human examiner logic. We prioritize key terms, logical flow, and method marks in subjects like Mathematics and Science. This ensures that students learn <em>how</em> to score marks, not just the correct final answer.
                    </p>
                </div>
             </div>

             {/* 3. Privacy */}
             <div className="flex flex-col md:flex-row gap-8 items-start">
                <div className="bg-zinc-100 p-4 rounded-xl shrink-0">
                    <Lock className="w-8 h-8 text-zinc-900" />
                </div>
                <div>
                    <h3 className="text-xl font-bold mb-3">Data Privacy</h3>
                    <p className="text-muted-foreground leading-relaxed mb-4">
                        We take student data privacy seriously.
                    </p>
                    <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
                        <li>We do not sell student data to third parties.</li>
                        <li>We do not display external advertisements.</li>
                        <li>Student progress data is visible only to the student and their authorized parent/guardian.</li>
                        <li>All data is encrypted in transit and at rest.</li>
                    </ul>
                </div>
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
