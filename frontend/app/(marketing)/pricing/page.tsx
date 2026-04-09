import Link from "next/link";
import { CheckCircle2, XCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { WaitlistHeroCTA } from "@/components/waitlist-hero-cta";
import { TIER_CONFIG } from "@/lib/subscription";

// Feature rows shown on every card
const FEATURES = [
  { key: "unlimited", label: "Unlimited AI-marked questions" },
  { key: "exam_mode", label: "Full exam mode with timer" },
  { key: "handwriting", label: "Handwriting / photo upload" },
  { key: "progress", label: "Detailed progress tracking" },
  { key: "parent", label: "Parent progress reports" },
] as const;

type FeatureKey = (typeof FEATURES)[number]["key"];

const TIER_FEATURES: Record<string, Record<FeatureKey, boolean>> = {
  starter: {
    unlimited: false,
    exam_mode: false,
    handwriting: false,
    progress: false,
    parent: false,
  },
  standard: {
    unlimited: true,
    exam_mode: true,
    handwriting: true,
    progress: true,
    parent: false,
  },
  bundle: {
    unlimited: true,
    exam_mode: true,
    handwriting: true,
    progress: true,
    parent: false,
  },
  all_subjects: {
    unlimited: true,
    exam_mode: true,
    handwriting: true,
    progress: true,
    parent: true,
  },
};

const TIER_ORDER = ["starter", "standard", "bundle", "all_subjects"] as const;

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-20">
          <div className="max-w-4xl mx-auto text-center mb-16">
            <h1 className="text-calm-h1 mb-6 text-foreground">
              Simple pricing,{" "}
              <br className="hidden md:block" />
              focused on results.
            </h1>
            <p className="text-calm-body max-w-2xl mx-auto">
              Start free. Upgrade when you need more subjects or exam mode. No hidden fees. Cancel anytime.
            </p>
            <div className="mt-8">
              <WaitlistHeroCTA
                compact
                buttonClassName="h-14 px-10 text-lg rounded-full w-full sm:w-auto"
                formClassName="mt-5 rounded-3xl border border-border/60 bg-background p-5 text-left shadow-sm"
              />
            </div>
          </div>

          <div className="max-w-6xl mx-auto grid md:grid-cols-4 gap-6">
            {TIER_ORDER.map((tierId) => {
              const tier = TIER_CONFIG[tierId];
              const features = TIER_FEATURES[tierId];
              const isPopular = tierId === "standard";

              return (
                <Card
                  key={tierId}
                  className={`p-6 rounded-[2rem] flex flex-col relative overflow-hidden ${
                    isPopular
                      ? "border-primary ring-1 ring-primary shadow-2xl shadow-primary/10"
                      : "border-border bg-zinc-50"
                  }`}
                >
                  {isPopular && (
                    <div className="absolute top-0 inset-x-0 h-1 bg-primary" />
                  )}
                  {isPopular && (
                    <span className="absolute top-3 right-3 text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full font-semibold">
                      Popular
                    </span>
                  )}

                  <div className="mb-6">
                    <h3 className="text-base font-bold text-foreground mb-2">{tier.label}</h3>
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="text-3xl font-bold tracking-tight">
                        {tier.price === 0 ? "Free" : `$${tier.price}`}
                      </span>
                      {tier.price > 0 && (
                        <span className="text-muted-foreground text-sm">/mo</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {tier.subjects}
                      {tier.dailyLimit !== null && ` · ${tier.dailyLimit} questions/day`}
                    </p>
                  </div>

                  <ul className="space-y-3 mb-6 flex-1">
                    {FEATURES.map(({ key, label }) => (
                      <li key={key} className="flex items-start gap-2 text-sm">
                        {features[key] ? (
                          <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-4 h-4 text-muted-foreground/40 shrink-0 mt-0.5" />
                        )}
                        <span
                          className={
                            features[key]
                              ? "font-medium text-zinc-700"
                              : "text-muted-foreground/60"
                          }
                        >
                          {label}
                        </span>
                      </li>
                    ))}
                  </ul>

                  <Link href="/register">
                    <Button
                      className={`w-full rounded-full h-11 font-bold ${
                        isPopular
                          ? "bg-primary hover:bg-primary/90"
                          : "bg-zinc-200 text-zinc-900 hover:bg-zinc-300"
                      }`}
                    >
                      {tier.price === 0 ? "Start free" : `Get ${tier.label}`}
                    </Button>
                  </Link>
                </Card>
              );
            })}
          </div>

          <div className="max-w-3xl mx-auto mt-20 text-center">
            <h3 className="text-lg font-semibold mb-4">Why we charge what we charge</h3>
            <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
              Quality exam preparation requires serious AI infrastructure. We do not sell your data.
              We do not serve ads. Your subscription directly funds AI marking, new papers, and a
              distraction-free learning environment.
            </p>
          </div>
        </section>
      </main>

      <footer className="py-12 px-6 border-t border-border mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <Link href="/" className="text-lg font-bold tracking-tight text-foreground">
              ZimPrep
            </Link>
            <nav className="flex gap-6 text-sm font-medium text-muted-foreground">
              <Link href="#" className="hover:text-foreground">Privacy</Link>
              <Link href="#" className="hover:text-foreground">Terms</Link>
            </nav>
          </div>
          <p className="text-sm text-muted-foreground w-full md:w-auto text-center md:text-right">
            &copy; {new Date().getFullYear()} ZimPrep
          </p>
        </div>
      </footer>
    </div>
  );
}
