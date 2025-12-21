"use client";

import { useEffect, useRef, useState } from "react";
// Keep Serif only for the exam paper content to mimic real papers
import { IBM_Plex_Serif } from "next/font/google"; 
import { evaluatePhysicsP1Answer, type EvalResult } from "@/lib/evaluator";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Zap, Lightbulb } from "lucide-react";

const serif = IBM_Plex_Serif({ subsets: ["latin"], weight: ["400", "500"] });

export default function SamplePractice() {
  const answerRef = useRef<HTMLTextAreaElement | null>(null);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [hintOpen, setHintOpen] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      answerRef.current?.focus();
    }, 150);
    return () => clearTimeout(t);
  }, []);

  return (
    <main className="min-h-screen bg-background text-foreground pt-32 pb-24">
      
      {/* Header Section */}
      <section className="mx-auto max-w-7xl px-6 mb-12">
          <div className="max-w-2xl">
            <h1 className="text-calm-h2 mb-4">Sample Practice.</h1>
            <p className="text-calm-body">Experience the Examiner&apos;s Edge engine.</p>
          </div>
      </section>

      <section className="mx-auto max-w-7xl px-6">
        <div className="panel p-0 md:p-0 grid grid-cols-1 lg:grid-cols-[1fr_420px] divide-y lg:divide-y-0 lg:divide-x divide-border shadow-2xl">
            
            {/* Question Panel */}
            <div className="p-8 md:p-12 bg-white">
              <div className="flex items-center justify-between pb-6 mb-8 border-b border-border/40">
                <div className="flex items-center gap-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full">
                    <Zap className="w-3 h-3 text-primary" />
                    <span className="text-xs font-bold text-primary">Physics P1</span>
                  </div>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs font-medium text-muted-foreground">Section A</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-100 rounded-full">
                  <span className="text-xs font-bold text-zinc-700">7 marks</span>
                </div>
              </div>
              
              {/* Exam Content - Using Serif to mimic paper */}
              <div className={`${serif.className} max-w-3xl text-sm md:text-base leading-relaxed text-zinc-900 mb-8`}>
                <p className="mb-6">
                  A block of mass <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">m</code> rests on a rough horizontal surface. A constant horizontal force <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">F</code> is applied. The coefficient of kinetic friction is <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">μ</code>.
                </p>
                <ol className="list-decimal ml-6 space-y-4">
                  <li>
                    Draw a clearly labelled free–body diagram for the block while it moves. (3)
                  </li>
                  <li>
                    Using Newton&apos;s second law, derive the acceleration in terms of <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">F</code>, <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">m</code>, and <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[13px] font-mono">μ</code>. (4)
                  </li>
                </ol>
              </div>

              <div className="p-4 bg-primary/5 border border-primary/20 rounded-2xl">
                <p className="text-xs text-foreground/80 leading-relaxed font-medium">
                  <span className="text-primary font-bold block mb-1">Marking guide:</span> Method marks for correct force diagram; application of <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">ΣF = ma</code> and friction model <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">f = μmg</code>.
                </p>
              </div>
            </div>

            {/* Answer Panel */}
            <div className="p-8 md:p-12 bg-zinc-50/50 flex flex-col">
              <label htmlFor="answer" className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-4">Your answer</label>
              <textarea
                id="answer"
                ref={answerRef}
                className="w-full flex-1 min-h-[300px] resize-none rounded-2xl border border-input bg-white p-6 text-sm md:text-base text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all font-mono leading-relaxed"
                placeholder="Begin with forces, then apply ΣF = ma…"
              />
              
              <div className="mt-6 flex items-center justify-between">
                <button
                  onClick={() => setHintOpen(!hintOpen)}
                  className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-primary transition-colors"
                >
                  <Lightbulb className="w-4 h-4" />
                  {hintOpen ? "Hide hint" : "Show hint"}
                </button>
                <Button
                  onClick={() => {
                    const text = answerRef.current?.value || "";
                    const result = evaluatePhysicsP1Answer(text);
                    setEvalResult(result);
                  }}
                  className="btn-primary"
                >
                  Submit for check
                </Button>
              </div>

              {hintOpen && (
                <div className="mt-6 p-4 bg-yellow-50/50 border border-yellow-200/50 rounded-2xl animate-in fade-in slide-in-from-top-2">
                  <p className="text-xs text-yellow-800 leading-relaxed">
                    <strong>Hint:</strong> Start by drawing all forces (weight down, normal up, applied force, friction). Then apply Newton&apos;s second law: <code className="bg-white/50 px-1 py-0.5 rounded text-[10px] font-mono">ΣF = ma</code>, use <code className="bg-white/50 px-1 py-0.5 rounded text-[10px] font-mono">f = μN = μmg</code> for friction.
                  </p>
                </div>
              )}

              {evalResult && (
                <Card className="mt-6 border-primary/20 bg-primary/5 animate-in zoom-in-95 duration-300 shadow-none">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3 mb-4">
                      {evalResult.totalEarned === evalResult.totalMax ? (
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="text-sm font-bold text-foreground">
                          Quick check: {evalResult.totalEarned}/{evalResult.totalMax} marks
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {evalResult.totalEarned === evalResult.totalMax
                            ? "Excellent work! All marks earned."
                            : "You're on the right track. Check the breakdown below."}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2 bg-white rounded-xl p-3 border border-primary/10">
                      {evalResult.details.map((d) => (
                        <div key={d.key} className="flex items-center justify-between text-xs">
                          <span className="text-foreground/80 font-medium">{d.key}</span>
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 bg-zinc-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${(d.earned / d.max) * 100}%` }}
                              />
                            </div>
                            <span className="font-bold text-foreground">{d.earned}/{d.max}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
        </div>
      </section>

      {/* Trust Cards */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
              { icon: CheckCircle2, title: "National Standards", text: "Questions aligned with exam boards." },
              { icon: Zap, title: "Instant Feedback", text: "See marks awarded immediately." },
              { icon: Lightbulb, title: "Learn Better", text: "Understand examiner expectations." }
          ].map((item, i) => (
             <Card key={i} className="bg-card border-border/40 hover:border-primary/30 transition-all duration-300 rounded-[2rem] p-6 shadow-sm">
                 <div className="text-center">
                    <div className="w-12 h-12 mx-auto bg-primary/10 rounded-full flex items-center justify-center mb-4">
                        <item.icon className="w-6 h-6 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">{item.text}</p>
                 </div>
             </Card>
          ))}
        </div>
      </section>

      {/* CTA Footer */}
      <section className="text-center pb-24 px-6">
        <h2 className="text-calm-h3 mb-6">Ready to practice more?</h2>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button className="btn-primary h-12 px-8" onClick={() => window.location.reload()}>
            Try another question
          </Button>
          <Button variant="outline" className="h-12 px-8 rounded-full border-border text-muted-foreground hover:text-foreground hover:bg-zinc-50">
            Save progress
          </Button>
        </div>
      </section>
    </main>
  );
}
