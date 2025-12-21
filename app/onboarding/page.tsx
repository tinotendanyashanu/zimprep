"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Stepper } from "@/components/onboarding/stepper";
import { StepLevel } from "@/components/onboarding/step-level";
import { StepSubjects } from "@/components/onboarding/step-subjects";
import { StepGoal } from "@/components/onboarding/step-goal";
import { StepSummary } from "@/components/onboarding/step-summary";
import { Button } from "@/components/ui/button";
import { ChevronRight, ChevronLeft } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  
  // State
  const [level, setLevel] = useState<string>("");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [goal, setGoal] = useState<string>("");

  // Check auth
  useEffect(() => {
     const isAuth = localStorage.getItem("isAuthenticated");
     if (!isAuth) {
         router.replace("/login");
     }
  }, [router]);

  const handleNext = () => {
    if (currentStep < 4) setCurrentStep(c => c + 1);
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(c => c - 1);
  };

  const handleFinish = () => {
    // Save everything
    localStorage.setItem("onboarding_completed", "true");
    localStorage.setItem("user_profile", JSON.stringify({ level, subjects, goal }));
    
    // Transition effect (Optional KPI boost)
    // For now, immediate redirect
    router.push("/dashboard");
  };

  // Validation for Next Button
  const canProceed = () => {
      if (currentStep === 1) return level !== "";
      if (currentStep === 2) return subjects.length > 0;
      if (currentStep === 3) return goal !== "";
      return true;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center py-12 px-6">
      
      {/* Header */}
      <div className="w-full max-w-4xl flex justify-center mb-8">
         <h1 className="text-xl font-bold tracking-tight text-primary">ZimPrep Setup</h1>
      </div>

      <Stepper 
        currentStep={currentStep} 
        steps={[
            { id: 1, label: "Level" }, 
            { id: 2, label: "Subjects" }, 
            { id: 3, label: "Goal" }, 
            { id: 4, label: "Review" }
        ]} 
      />

      <div className="w-full max-w-3xl flex-1 flex flex-col">
        <div className="flex-1">
            {currentStep === 1 && <StepLevel value={level} onChange={setLevel} />}
            {currentStep === 2 && <StepSubjects selected={subjects} onChange={setSubjects} />}
            {currentStep === 3 && <StepGoal value={goal} onChange={setGoal} />}
            {currentStep === 4 && (
                <StepSummary 
                    level={level} 
                    subjects={subjects} 
                    goal={goal} 
                    onConfirm={handleFinish}
                    onEdit={setCurrentStep}
                />
            )}
        </div>

        {/* Navigation Buttons (Hide on step 4 as it has its own CTA) */}
        {currentStep < 4 && (
             <div className="flex justify-between items-center mt-12 pt-6 border-t border-zinc-100 max-w-xl mx-auto w-full">
                <Button 
                    variant="ghost" 
                    onClick={handleBack} 
                    disabled={currentStep === 1}
                    className={currentStep === 1 ? "invisible" : ""}
                >
                    <ChevronLeft className="w-4 h-4 mr-2" /> Back
                </Button>
                <Button 
                    onClick={handleNext} 
                    disabled={!canProceed()}
                    className="btn-primary rounded-full px-8"
                >
                    Continue <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
            </div>
        )}
      </div>
    </div>
  );
}
