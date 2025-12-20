"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle2 } from "lucide-react";

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-20">
          <div className="max-w-4xl mx-auto text-center mb-16">
            <h1 className="text-calm-h1 mb-6 text-foreground">Simple pricing, <br className="hidden md:block"/>focused on results.</h1>
            <p className="text-calm-body max-w-2xl mx-auto">
              Choose the plan that fits your stage of preparation. No hidden fees. Cancel anytime.
            </p>
          </div>

          <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
            {[
              { 
                name: "Starter", 
                price: "$0", 
                desc: "Try before committing.", 
                features: [
                  "Access to sample papers", 
                  "Limited practice questions", 
                  "Basic result summary", 
                  "No time limit on trial"
                ] 
              },
              { 
                name: "Standard", 
                price: "$35", 
                desc: "Most popular choice.", 
                features: [  
                  "Full access to all subjects",
                  "Unlimited examiner-style marking",
                  "Detailed progress tracking",
                  "Mobile & Tablet friendly",
                  "Priority email support"
                ],
                popular: true 
              },
              { 
                name: "Prestige", 
                price: "$60", 
                desc: "Ideal for exam-year students.", 
                features: [
                  "Everything in Standard",
                  "AI-driven weakness analysis",
                  "Personalized revision schedule",
                  "Examiner commentary breakdown",
                  "Parent weekly progress report"
                ] 
              }
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
                      <li key={j} className="flex items-start gap-3 text-sm font-medium text-zinc-700">
                         <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                         <span className="leading-snug">{f}</span>
                      </li>
                   ))}
                </ul>
                <Button className={`w-full rounded-full h-12 font-bold ${plan.popular ? 'bg-primary hover:bg-primary/90' : 'bg-zinc-200 text-zinc-900 hover:bg-zinc-300'}`}>
                   Choose {plan.name}
                </Button>
              </Card>
            ))}
          </div>

          <div className="max-w-3xl mx-auto mt-20 text-center">
            <h3 className="text-lg font-semibold mb-4">Why we charge what we charge</h3>
            <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
              Quality education requires qualified examiners and robust technology. We do not sell your data. We do not serve ads. Your subscription directly funds the development of new content and the maintenance of a distraction-free learning environment.
            </p>
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
