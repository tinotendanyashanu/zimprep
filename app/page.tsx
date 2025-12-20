"use client";

import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, CheckCircle2, ChevronDown, Trophy, Shield, Zap } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      
      {/* 
        SECTION 1: HERO
        Primary Conversion Moment
      */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-calm-h1 mb-6 text-foreground">
            Master your exams <br className="hidden md:block" />
            with absolute confidence.
          </h1>
          {/* Clarification Line - Critical */}
          <p className="text-calm-body max-w-3xl mx-auto mb-10">
             Practice real exam papers with examiner-style marking, built strictly to ZIMSEC standards.
          </p>
          <div className="flex items-center justify-center gap-4 mb-20">
            <Button size="lg" className="btn-primary h-14 px-10 text-lg rounded-full">
              Start Free Trial
            </Button>
            <Button size="lg" variant="ghost" className="btn-secondary h-14 px-10 text-lg rounded-full text-foreground hover:bg-zinc-100">
              View Demo
            </Button>
          </div>
          
          {/* Hero Visual - Product First */}
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-border/20">
            <Image
              src="/hero-education.png"
              alt="Students learning with ZimPrep"
              width={1920}
              height={1080}
              className="w-full object-cover aspect-[21/9]"
              priority
            />
            {/* Floating UI Mockup overlay - Preserved from Design Lock */}
            <div className="absolute -bottom-12 -right-12 md:bottom-8 md:right-8 w-2/3 md:w-1/3 bg-background/90 backdrop-blur-xl p-6 rounded-2xl shadow-xl border border-white/20 hidden md:block">
              <div className="flex items-center gap-3 mb-4">
                 <div className="h-2 w-2 rounded-full bg-red-500"/>
                 <div className="h-2 w-2 rounded-full bg-yellow-500"/>
                 <div className="h-2 w-2 rounded-full bg-green-500"/>
              </div>
              <div className="space-y-3">
                <div className="h-2 bg-zinc-200 rounded-full w-3/4" />
                <div className="h-2 bg-zinc-200 rounded-full w-1/2" />
                <div className="mt-4 p-3 bg-primary/10 rounded-lg border border-primary/20">
                   <p className="text-xs font-bold text-primary">Examiner Note:</p>
                   <p className="text-[10px] text-muted-foreground mt-1">Key term &quot;dynamic equilibrium&quot; awarded 1 mark.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 
        SECTION 2: CREDIBILITY STRIP
        Trust Anchor. Text only.
      */}
      <section className="border-y border-border/40 py-8 bg-zinc-50/50">
         <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-center items-center gap-4 md:gap-24 text-center">
            <span className="text-sm md:text-base font-medium text-muted-foreground tracking-wide">Aligned with official ZIMSEC syllabus</span>
            <span className="hidden md:block w-1.5 h-1.5 rounded-full bg-zinc-300" />
            <span className="text-sm md:text-base font-medium text-muted-foreground tracking-wide">Structured using real past exam formats</span>
            <span className="hidden md:block w-1.5 h-1.5 rounded-full bg-zinc-300" />
            <span className="text-sm md:text-base font-medium text-muted-foreground tracking-wide">Marked using examiner-style logic</span>
         </div>
      </section>

      {/* 
        SECTION 3: FEATURE STORY 1 – EXAMINER’S EDGE
        Outcome first.
      */}
      <section id="features" className="py-24 md:py-32 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="order-2 md:order-1 bg-zinc-100 rounded-[2.5rem] p-8 md:p-12 aspect-square flex items-center justify-center overflow-hidden relative">
             <div className="absolute inset-0 bg-gradient-to-br from-zinc-100 to-zinc-200" />
             {/* Abstract representation of "Insight" (Locked Design) */}
             <div className="relative z-10 w-full max-w-sm bg-white rounded-2xl shadow-lg p-6 border border-zinc-100">
                <div className="flex justify-between items-center mb-6">
                   <span className="text-xs font-bold text-zinc-400 uppercase">Question 4(b)</span>
                   <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded">High Yield</span>
                </div>
                <h4 className="font-semibold text-lg mb-2">Define &quot;Osmosis&quot;</h4>
                <div className="space-y-2">
                   <p className="text-sm text-zinc-800 p-3 bg-zinc-50 rounded border border-zinc-100">Movement of water molecules...</p>
                   <div className="flex items-start gap-3 p-3 bg-green-50 rounded border border-green-100">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-green-700">Examiner Insight</p>
                        <p className="text-[10px] text-green-800/70">Must mention &quot;selectively permeable membrane&quot; for the second mark.</p>
                      </div>
                   </div>
                </div>
             </div>
          </div>
          <div className="order-1 md:order-2">
            <h2 className="text-calm-h2 mb-6">See your answers the way an examiner does.</h2>
            <p className="text-calm-body mb-8">
              Most students lose marks not because they do not know the content, but because they do not answer the way exams expect.
            </p>
            <p className="text-calm-body text-base">
              ZimPrep evaluates your answers using examiner-style logic, highlighting exactly where marks are gained or lost. You learn what to include, what to avoid, and how to structure answers for maximum credit.
            </p>
          </div>
        </div>
      </section>
      
      {/* 
        SECTION 4: FEATURE STORY 2 – GUIDED PRACTICE FLOW
        Process clarity.
      */}
      <section className="py-24 md:py-32 px-6 bg-zinc-50/30">
         <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
           <div className="order-1">
             <h2 className="text-calm-h2 mb-4">Practice exactly like the real exam.</h2>
             <p className="text-calm-body mb-6">
               Choose your subject and paper, then work through questions structured exactly like the final exam.
             </p>
             <p className="text-calm-body text-base">
               Timed practice, clear layouts, and realistic question progression help build confidence under exam conditions. No shortcuts. No random questions. Just disciplined preparation.
             </p>
           </div>
           {/* Visual: Structured exam-style practice (Locked Design) */}
           <div className="order-2 bg-zinc-100 rounded-[2.5rem] p-8 aspect-square flex items-center justify-center relative overflow-hidden">
              <div className="text-center space-y-4 w-full max-w-sm">
                 <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-sm border border-zinc-200">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    <span className="text-sm font-mono font-medium text-zinc-800">01:29:59 remaining</span>
                 </div>
                 <div className="bg-white rounded-xl p-6 shadow-lg border border-zinc-100 text-left w-full">
                    <div className="h-4 bg-zinc-100 rounded w-3/4 mb-3" />
                    <div className="h-4 bg-zinc-100 rounded w-1/2 mb-6" />
                    <div className="h-32 border-2 border-dashed border-zinc-200 rounded-lg flex items-center justify-center">
                       <span className="text-xs text-zinc-400">Type your answer here...</span>
                    </div>
                 </div>
              </div>
           </div>
        </div>
      </section>

      {/* 
        SECTION 5: FEATURE STORY 3 – ANALYTICS & FEEDBACK
        Measurement and reassurance.
      */}
      <section className="py-24 md:py-32 px-6 bg-zinc-50/50">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-calm-h2 mb-6">Know where you stand before exam day.</h2>
            <p className="text-calm-body mb-8">
              Track your progress across topics, papers, and attempts.
            </p>
             <p className="text-calm-body text-base mb-8">
              ZimPrep shows your strengths, exposes gaps, and highlights patterns that need attention, so revision time is focused where it matters most. No guessing. No false confidence.
            </p>
            <Button variant="link" className="p-0 text-primary font-bold text-lg h-auto hover:no-underline hover:opacity-80">
              Explore Analytics <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
          <div className="bg-white rounded-[2.5rem] p-8 md:p-12 shadow-2xl shadow-zinc-200/50 aspect-square flex flex-col justify-center relative border border-zinc-100 overflow-hidden">
             {/* Chart UI Mockup (Locked Design) */}
             <div className="flex items-end justify-between h-48 gap-4 px-4 mb-8">
                {[40, 65, 35, 85, 55, 90].map((h, i) => (
                   <div key={i} className="w-full bg-zinc-100 rounded-t-lg relative group">
                      <div 
                        className="absolute bottom-0 left-0 w-full bg-primary rounded-t-lg transition-all duration-1000"
                        style={{ height: `${h}%`, opacity: (i+4)/10 }}
                      />
                   </div>
                ))}
             </div>
             <div className="text-center">
                <p className="text-3xl font-bold text-zinc-900 mb-1">92%</p>
                <p className="text-sm font-medium text-zinc-500 uppercase tracking-wide">Readiness Index</p>
             </div>
          </div>
        </div>
      </section>

      {/* 
        SECTION 6: HOW IT WORKS (Micro-Flow)
        Process clarity.
      */}
      <section className="py-24 md:py-32 px-6 bg-zinc-900 text-white">
         <div className="max-w-4xl mx-auto text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">How ZimPrep works.</h2>
         </div>
         <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-12 text-center relative">
            <div className="space-y-4">
               <span className="text-sm font-mono text-zinc-500">01</span>
               <h3 className="text-xl font-bold">Choose a subject.</h3>
               <p className="text-zinc-400 text-sm leading-relaxed">Select the exact subject and paper you are preparing for.</p>
            </div>
             <div className="space-y-4">
               <span className="text-sm font-mono text-zinc-500">02</span>
               <h3 className="text-xl font-bold">Practice real exam papers.</h3>
               <p className="text-zinc-400 text-sm leading-relaxed">Answer questions in exam-style format and timing.</p>
            </div>
             <div className="space-y-4">
               <span className="text-sm font-mono text-zinc-500">03</span>
               <h3 className="text-xl font-bold">Get feedback and insights.</h3>
               <p className="text-zinc-400 text-sm leading-relaxed">See where marks were earned, lost, and how to improve.</p>
            </div>
         </div>
      </section>

      {/* 
        SECTION 7: SOCIAL PROOF
        Quiet Confidence.
      */}
      <section className="border-y border-border/40 py-12 bg-zinc-50/50">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-4">Trusted by students preparing for real exams</p>
          <p className="text-sm text-muted-foreground mb-8">Used by focused learners who want structured preparation, not shortcuts.</p>
          <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
             {/* Text placeholders for logos */}
             <span className="text-xl font-serif font-bold text-zinc-800">Harare International</span>
             <span className="text-xl font-serif font-bold text-zinc-800">Chisipite</span>
             <span className="text-xl font-serif font-bold text-zinc-800">St. George&apos;s</span>
             <span className="text-xl font-serif font-bold text-zinc-800">Peterhouse</span>
          </div>
        </div>
      </section>

      {/* 
        SECTION 8: PRICING
        Clarity > Persuasion.
      */}
      <section id="pricing" className="py-24 md:py-32 px-6">
        <div className="max-w-4xl mx-auto text-center mb-16">
          <h2 className="text-calm-h2 mb-6">Simple pricing, focused on results.</h2>
          <p className="text-calm-body">Simple monthly access per subject.</p>
        </div>
        
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
          {[
            { name: "Starter", price: "$0", desc: "Try before committing.", features: ["Limited practice access", "Explore the platform", "Try before committing"] },
            { name: "Standard", price: "$35", desc: "Most popular choice.", features: ["Full subject access", "Examiner-style marking", "Progress tracking"], popular: true },
            { name: "Prestige", price: "$60", desc: "Ideal for exam-year students.", features: ["Everything in Standard", "Priority insights", "Ideal for exam-year students"] }
          ].map((plan, i) => (
            <Card key={i} className={`p-8 rounded-[2rem] flex flex-col ${plan.popular ? 'border-primary ring-1 ring-primary shadow-2xl shadow-primary/10 relative overflow-hidden' : 'border-border bg-zinc-50'}`}>
              {plan.popular && <div className="absolute top-0 inset-x-0 h-1 bg-primary" />}
              <div className="mb-8">
                 <h3 className="text-lg font-bold text-foreground mb-2">{plan.name}</h3>
                 <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-4xl font-bold tracking-tight">{plan.price}</span>
                    <span className="text-muted-foreground text-sm">/mo</span>
                 </div>
                 <p className="text-sm text-muted-foreground">{plan.desc}</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                 {plan.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-3 text-sm font-medium text-zinc-700">
                       <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                       {f}
                    </li>
                 ))}
              </ul>
              <Button className={`w-full rounded-full h-12 font-bold ${plan.popular ? 'bg-primary hover:bg-primary/90' : 'bg-zinc-200 text-zinc-900 hover:bg-zinc-300'}`}>
                 Choose {plan.name}
              </Button>
            </Card>
          ))}
        </div>
      </section>

      {/* 
        SECTION 9: FAQ
        Ordered for Trust.
      */}
      <section className="py-24 px-6 bg-zinc-50 border-t border-border/40">
         <div className="max-w-3xl mx-auto">
            <h2 className="text-calm-h2 mb-12 text-center">Common questions.</h2>
            <Accordion type="single" collapsible className="w-full space-y-4">
              {[
                { q: "Is ZimPrep aligned with ZIMSEC?", a: "Yes. All subjects and papers are structured strictly according to the official ZIMSEC syllabus and exam formats." },
                { q: "How is marking done?", a: "Answers are evaluated using examiner-style logic that reflects how marks are awarded in real exams." },
                { q: "Can my child use this on a phone or tablet?", a: "Yes. ZimPrep works on phones, tablets, and computers." },
                { q: "Is there a free trial?", a: "Yes. You can start with a free trial before choosing a plan." }
              ].map((item, i) => (
                <AccordionItem key={i} value={`item-${i}`} className="border-b border-zinc-200 px-4">
                  <AccordionTrigger className="text-lg font-medium text-zinc-800 hover:text-primary hover:no-underline py-6">
                    {item.q}
                  </AccordionTrigger>
                  <AccordionContent className="text-zinc-500 text-base pb-6 leading-relaxed">
                    {item.a}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
         </div>
      </section>

      {/* 
        SECTION 10: FINAL CTA
        Decision Moment.
      */}
      <section className="py-32 px-6 text-center">
         <div className="max-w-2xl mx-auto">
            <h2 className="text-calm-h2 mb-8">Prepare the way exams are actually marked.</h2>
            <Button size="lg" className="btn-primary h-14 px-12 text-lg rounded-full shadow-lg hover:shadow-xl transition-all">
              Start Free Trial
            </Button>
         </div>
      </section>

      {/* Minimal Footer */}
      <footer className="py-12 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
           <div className="flex flex-col md:flex-row items-center gap-8">
              <span className="text-lg font-bold tracking-tight text-foreground">ZimPrep</span>
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
