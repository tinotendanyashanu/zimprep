import { LucideIcon, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Step {
  id: number;
  label: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <div className="w-full max-w-md mx-auto mb-12">
      <div className="relative flex items-center justify-between">
        {/* Progress Line */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-zinc-100 rounded-full -z-10" />
        <div 
            className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-primary rounded-full -z-10 transition-all duration-300"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((step) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;

          return (
            <div key={step.id} className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 border-2",
                  isCompleted
                    ? "bg-primary border-primary text-white"
                    : isCurrent
                    ? "bg-white border-primary text-primary shadow-sm ring-4 ring-primary/10"
                    : "bg-white border-zinc-200 text-zinc-400"
                )}
              >
                {isCompleted ? <Check className="w-4 h-4" /> : step.id}
              </div>
              <span 
                className={cn(
                    "text-[10px] font-medium uppercase tracking-wider absolute top-10 w-32 text-center transition-colors duration-300",
                    isCurrent ? "text-foreground" : "text-muted-foreground opacity-0"
                )}
               >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
