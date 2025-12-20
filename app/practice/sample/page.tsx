"use client";

import { useEffect, useRef, useState } from "react";
import { IBM_Plex_Serif } from "next/font/google";
import { evaluatePhysicsP1Answer, type EvalResult } from "../../../lib/evaluator";
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
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 via-white to-zinc-50 text-zinc-900">
      <section className="mx-auto max-w-7xl px-6 pt-20 pb-20 animate-fade-in">
        <div className="relative rounded-2xl border border-zinc-200/50 bg-gradient-to-br from-white to-zinc-50/50 shadow-xl overflow-hidden hover-lift">
          {/* Header */}
          <div className="h-10 border-b border-zinc-200 flex items-center justify-between px-6 bg-gradient-to-r from-zinc-50 to-white">
            <div className="text-xs font-bold text-[#065F46] uppercase tracking-wider">Practice Mode</div>
            <div className="text-xs text-zinc-500">zimprep.com/practice/sample</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[1fr_420px]">
            {/* Question Panel */}
            <div className="p-8 border-b md:border-b-0 md:border-r border-zinc-200">
              <div className="flex items-center justify-between pb-6 mb-8 border-b border-zinc-200">
                <div className="flex items-center gap-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#065F46]/10 rounded-lg">
                    <Zap className="w-3 h-3 text-[#065F46]" />
                    <span className="text-xs font-semibold text-[#065F46]">Physics P1</span>
                  </div>
                  <span className="text-xs text-zinc-500">•</span>
                  <span className="text-xs text-zinc-500">Section A</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 rounded-lg">
                  <span className="text-xs font-bold text-emerald-700">7 marks</span>
                </div>
              </div>
              <div className={`${serif.className} max-w-3xl text-sm leading-relaxed text-zinc-800 mb-6`}>
                <p className="mb-4">
                  A block of mass <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">m</code> rests on a rough horizontal surface. A constant horizontal force <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">F</code> is applied. The coefficient of kinetic friction is <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">μ</code>.
                </p>
                <ol className="list-decimal ml-6 space-y-3">
                  <li>
                    Draw a clearly labelled free–body diagram for the block while it moves. (3)
                  </li>
                  <li>
                    Using Newton's second law, derive the acceleration in terms of <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">F</code>, <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">m</code>, and <code className="bg-zinc-100 px-1.5 py-0.5 rounded text-[11px] font-mono">μ</code>. (4)
                  </li>
                </ol>
              </div>
              <div className="p-4 bg-[#065F46]/5 border border-[#065F46]/20 rounded-lg">
                <p className="text-xs text-zinc-700 leading-relaxed">
                  <strong className="text-zinc-900 block mb-2">Marking guide:</strong> Method marks for correct force diagram; application of <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">ΣF = ma</code> and friction model <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">f = μmg</code>.
                </p>
              </div>
            </div>

            {/* Answer Panel */}
            <div className="p-8 bg-gradient-to-br from-white via-[#065F46]/1 to-[#065F46]/3">
              <label htmlFor="answer" className="block text-xs font-bold text-zinc-900 uppercase tracking-wider mb-4">Your answer</label>
              <textarea
                id="answer"
                ref={answerRef}
                rows={12}
                className="w-full resize-none rounded-lg border border-zinc-300 bg-white p-4 text-sm text-zinc-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#065F46]/50 focus:border-transparent"
                placeholder="Begin with forces, then apply ΣF = ma…"
              />
              <div className="mt-4 flex items-center justify-between">
                <button
                  onClick={() => setHintOpen(!hintOpen)}
                  className="flex items-center gap-2 text-xs font-medium text-[#065F46] hover:text-[#055444] transition-colors"
                >
                  <Lightbulb className="w-3 h-3" />
                  {hintOpen ? "Hide hint" : "Show hint"}
                </button>
                <Button
                  size="sm"
                  onClick={() => {
                    const text = answerRef.current?.value || "";
                    const result = evaluatePhysicsP1Answer(text);
                    setEvalResult(result);
                  }}
                  className="bg-[#065F46] hover:bg-[#055444]"
                >
                  Submit for check
                </Button>
              </div>
              {hintOpen && (
                <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg animate-slide-down">
                  <p className="text-xs text-amber-900 leading-relaxed">
                    <strong>Hint:</strong> Start by drawing all forces (weight down, normal up, applied force, friction). Then apply Newton's second law: <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">ΣF = ma</code>, use <code className="bg-white px-1 py-0.5 rounded text-[10px] font-mono">f = μN = μmg</code> for friction.
                  </p>
                </div>
              )}
              {evalResult && (
                <Card className="mt-4 border-[#065F46]/20 bg-gradient-to-br from-[#065F46]/5 to-transparent animate-scale-in">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3 mb-4">
                      {evalResult.totalEarned === evalResult.totalMax ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="text-sm font-bold text-zinc-900">
                          Quick check: {evalResult.totalEarned}/{evalResult.totalMax} marks
                        </div>
                        <p className="text-xs text-zinc-600 mt-1">
                          {evalResult.totalEarned === evalResult.totalMax
                            ? "Excellent work! All marks earned."
                            : "You're on the right track. Check the breakdown below."}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2 bg-white rounded-md p-3">
                      {evalResult.details.map((d) => (
                        <div key={d.key} className="flex items-center justify-between text-xs">
                          <span className="text-zinc-700">{d.key}</span>
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-12 bg-zinc-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-[#065F46] rounded-full"
                                style={{ width: `${(d.earned / d.max) * 100}%` }}
                              />
                            </div>
                            <span className="font-semibold text-zinc-900">{d.earned}/{d.max}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-500 mt-3">Feedback is indicative. Review with your teacher for detailed guidance.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="mx-auto max-w-5xl px-6 py-16 animate-slide-up">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="animate-stagger-0">
            <Card className="hover-lift h-full bg-gradient-to-br from-white to-[#065F46]/5 border-[#065F46]/20">
              <CardContent className="pt-8 text-center">
                <CheckCircle2 className="w-8 h-8 text-[#065F46] mx-auto mb-4" />
                <h3 className="font-semibold text-zinc-900 mb-2">National standards</h3>
                <p className="text-sm text-zinc-600">Questions aligned with exam boards</p>
              </CardContent>
            </Card>
          </div>
          <div className="animate-stagger-1">
            <Card className="hover-lift h-full bg-gradient-to-br from-white to-[#065F46]/5 border-[#065F46]/20">
              <CardContent className="pt-8 text-center">
                <Zap className="w-8 h-8 text-[#065F46] mx-auto mb-4" />
                <h3 className="font-semibold text-zinc-900 mb-2">Instant feedback</h3>
                <p className="text-sm text-zinc-600">See marks awarded immediately</p>
              </CardContent>
            </Card>
          </div>
          <div className="animate-stagger-2">
            <Card className="hover-lift h-full bg-gradient-to-br from-white to-[#065F46]/5 border-[#065F46]/20">
              <CardContent className="pt-8 text-center">
                <Lightbulb className="w-8 h-8 text-[#065F46] mx-auto mb-4" />
                <h3 className="font-semibold text-zinc-900 mb-2">Learn better</h3>
                <p className="text-sm text-zinc-600">Understand examiner expectations</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="mx-auto max-w-5xl px-6 py-16 text-center animate-slide-up">
        <h2 className="text-2xl font-bold text-zinc-900 mb-4">Ready to practice more?</h2>
        <p className="text-zinc-600 mb-6 max-w-md mx-auto">Start with another question or save your progress to practice later.</p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button asChild className="bg-gradient-to-r from-[#065F46] to-emerald-600 hover:from-[#055444] hover:to-emerald-700">
            <a href="/practice/sample">Try another question</a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/signup">Save progress</a>
          </Button>
        </div>
      </section>
    </main>
  );
}
