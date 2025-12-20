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
      
      {/* Hero Section - Radical Minimalism */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-calm-h1 mb-6 text-foreground">
            Master your exams <br className="hidden md:block" />
            with absolute confidence.
          </h1>
          <p className="text-calm-body max-w-2xl mx-auto mb-10">
            ZimPrep replaces anxiety with strategy. The only platform that teaches you the specific &quot;Mark Scheme DNA&quot; needed to secure an A.
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
            {/* Floating UI Mockup overlay */}
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

      {/* Social Proof - Quiet & Credible */}
      <section className="border-y border-border/40 py-12 bg-zinc-50/50">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-8">Trusted by Zimbabwe&apos;s Top Institutes</p>
          <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
             {/* Text placeholders for logos to keep it minimal/clean strictly as requested */}
             <span className="text-xl font-serif font-bold text-zinc-800">Harare International</span>
             <span className="text-xl font-serif font-bold text-zinc-800">Chisipite</span>
             <span className="text-xl font-serif font-bold text-zinc-800">St. George&apos;s</span>
             <span className="text-xl font-serif font-bold text-zinc-800">Peterhouse</span>
          </div>
        </div>
      </section>

      {/* Feature 1: Examiner's Edge */}
      <section id="features" className="py-24 md:py-32 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div className="order-2 md:order-1 bg-zinc-100 rounded-[2.5rem] p-8 md:p-12 aspect-square flex items-center justify-center overflow-hidden relative">
             <div className="absolute inset-0 bg-gradient-to-br from-zinc-100 to-zinc-200" />
             {/* Abstract representation of "Insight" */}
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
            <h2 className="text-calm-h2 mb-6">Think like the examiner.</h2>
            <p className="text-calm-body mb-8">
              We decode the &quot;Mark Scheme DNA&quot; for every subject. Don&apos;t just memorize facts—learn exactly which keywords trigger the marks.
            </p>
            <div className="flex flex-col gap-4">
               <div className="flex items-center gap-4">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                    <Zap className="w-4 h-4" />
                  </span>
                  <span className="text-lg font-medium text-zinc-700">Instant keyword validation</span>
               </div>
               <div className="flex items-center gap-4">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                    <Shield className="w-4 h-4" />
                  </span>
                  <span className="text-lg font-medium text-zinc-700">Official syllabus alignment</span>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature 2: Analytics */}
      <section className="py-24 md:py-32 px-6 bg-zinc-50/50">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-calm-h2 mb-6">Data, not guesswork.</h2>
            <p className="text-calm-body mb-8">
              Visualise your progress with surgical precision. Identify your weak topics instantly and focus your energy where it matters most.
            </p>
            <Button variant="link" className="p-0 text-primary font-bold text-lg h-auto hover:no-underline hover:opacity-80">
              Explore Analytics <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
          <div className="bg-white rounded-[2.5rem] p-8 md:p-12 shadow-2xl shadow-zinc-200/50 aspect-square flex flex-col justify-center relative border border-zinc-100 overflow-hidden">
             {/* Chart UI Mockup */}
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

      {/* Pricing Section - Minimalist */}
      <section id="pricing" className="py-24 md:py-32 px-6">
        <div className="max-w-4xl mx-auto text-center mb-16">
          <h2 className="text-calm-h2 mb-6">Simple, transparent pricing.</h2>
          <p className="text-calm-body">Invest in your future for the price of a single textbook.</p>
        </div>
        
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
          {[
            { name: "Basic", price: "$15", desc: "Essential for revision.", features: ["1 Subject", "Past Paper Archive", "Basic Analytics"] },
            { name: "Pro", price: "$35", desc: "Most popular choice.", features: ["3 Subjects", "AI Examiner Feedback", "Predictive Grade", "Priority Support"], popular: true },
            { name: "Unlimited", price: "$60", desc: "Total academic freedom.", features: ["All Subjects", "1-on-1 Mentorship", "Lifetime Access", "Parent Dashboard"] }
          ].map((plan, i) => (
            <Card key={i} className={`p-8 rounded-[2rem] flex flex-col ${plan.popular ? 'border-primary ring-1 ring-primary shadow-2xl shadow-primary/10 relative overflow-hidden' : 'border-border bg-zinc-50'}`}>
              {plan.popular && <div className="absolute top-0 inset-x-0 h-1 bg-primary" />}
              <div className="mb-8">
                 <h3 className="text-lg font-bold text-foreground mb-2">{plan.name}</h3>
                 <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-4xl font-bold tracking-tight">{plan.price}</span>
                    <span className="text-muted-foreground text-sm">/term</span>
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

      {/* FAQ Dropdowns */}
      <section className="py-24 px-6 bg-zinc-50 border-t border-border/40">
         <div className="max-w-3xl mx-auto">
            <h2 className="text-calm-h3 mb-12 text-center">Frequently asked questions</h2>
            <Accordion type="single" collapsible className="w-full space-y-4">
              {[
                { q: "Is this updated for the 2024/2025 syllabus?", a: "Yes. Our content team reviews ZIMSEC circulars weekly to ensure 100% alignment with the latest curriculum changes." },
                { q: "Can I access ZimPrep on my phone?", a: "Absolutely. ZimPrep is fully optimized for mobile devices, so you can study on the go." },
                { q: "How does the AI marking work?", a: "Our AI is trained on thousands of past examiner reports. It identifies keywords and structure, simulating a real marking session." },
                { q: "Do you offer school licenses?", a: "Yes, we partner with over 50 schools. Contact our sales team for institutional pricing." }
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
