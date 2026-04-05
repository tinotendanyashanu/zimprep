"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, BookOpen, GraduationCap, School } from "lucide-react";

export default function SubjectsPage() {
  const [activeBoard, setActiveBoard] = useState<"zimsec" | "cambridge">("zimsec");

  const zimsecLevels = [
    {
      title: "Grade 7 (ZIMSEC)",
      icon: <School className="w-6 h-6 text-zinc-600"/>,
      description: "Preparation for Grade 7 final exams.",
      subjects: [
        { name: "Mathematics", code: "G7-Math", papers: ["Paper 1", "Paper 2"], status: "Coming Soon" },
        { name: "English", code: "G7-Eng", papers: ["Paper 1", "Paper 2"], status: "Coming Soon" },
        { name: "General Paper", code: "G7-GP", papers: ["Paper 1"], status: "Coming Soon" },
        { name: "Indigenous Languages", code: "G7-IL", papers: ["Paper 1"], status: "Coming Soon" }
      ]
    },
    {
      title: "O-Level (Form 4)",
      icon: <BookOpen className="w-6 h-6 text-zinc-600"/>,
      description: "Core ZIMSEC O-Level syllabus coverage.",
      subjects: [
        { name: "Mathematics", code: "4004", papers: ["Paper 1 (Non-Calculator)", "Paper 2 (Structured)"], status: "Available" },
        { name: "English Language", code: "1122", papers: ["Paper 1 (Composition)", "Paper 2 (Comprehension)"], status: "Available" },
        { name: "Combined Science", code: "4003", papers: ["Paper 1 (Choice)", "Paper 2 (Theory)", "Paper 3 (Alt)"], status: "Available" },
        { name: "History", code: "2167", papers: ["Paper 1 (Africa)", "Paper 2 (World Affairs)"], status: "Coming Soon" },
        { name: "Geography", code: "2248", papers: ["Paper 1", "Paper 2"], status: "Coming Soon" },
        { name: "Accounts", code: "7110", papers: ["Paper 1", "Paper 2"], status: "Coming Soon" }
      ]
    },
    {
      title: "A-Level (Form 6)",
      icon: <GraduationCap className="w-6 h-6 text-zinc-600"/>,
      description: "Advanced Level preparation for university entry.",
      subjects: [
        { name: "Mathematics", code: "6042", papers: ["Pure Math 1", "Stats/Mech"], status: "Coming Soon" },
        { name: "Physics", code: "6030", papers: ["Multiple Choice", "Structured", "Practical"], status: "Coming Soon" },
        { name: "Chemistry", code: "6031", papers: ["Multiple Choice", "Structured", "Practical"], status: "Coming Soon" },
        { name: "Biology", code: "6032", papers: ["Multiple Choice", "Structured", "Practical"], status: "Coming Soon" }
      ]
    }
  ];

  const cambridgeLevels = [
    {
      title: "Cambridge IGCSE",
      icon: <BookOpen className="w-6 h-6 text-blue-600"/>,
      description: "Cambridge IGCSE — internationally recognised O Level equivalent.",
      subjects: [
        { name: "Mathematics", code: "0580", papers: ["Paper 1 (Core)", "Paper 2 (Extended)", "Paper 4 (Extended)"], status: "Coming Soon" },
        { name: "English as a Second Language", code: "0510", papers: ["Paper 1 (Reading)", "Paper 2 (Writing)", "Paper 3 (Listening)"], status: "Coming Soon" },
        { name: "Biology", code: "0610", papers: ["Paper 1 (MCQ)", "Paper 2 (Theory)", "Paper 6 (Alt Practical)"], status: "Coming Soon" },
        { name: "Chemistry", code: "0620", papers: ["Paper 1 (MCQ)", "Paper 2 (Theory)", "Paper 6 (Alt Practical)"], status: "Coming Soon" },
        { name: "Physics", code: "0625", papers: ["Paper 1 (MCQ)", "Paper 2 (Theory)", "Paper 6 (Alt Practical)"], status: "Coming Soon" },
        { name: "History", code: "0470", papers: ["Paper 1 (Core)", "Paper 2 (Depth Study)"], status: "Coming Soon" },
      ]
    },
    {
      title: "Cambridge AS & A Level",
      icon: <GraduationCap className="w-6 h-6 text-blue-600"/>,
      description: "Cambridge International AS & A Level — university entry preparation.",
      subjects: [
        { name: "Mathematics", code: "9709", papers: ["Pure Mathematics 1", "Pure Mathematics 2", "Statistics", "Mechanics"], status: "Coming Soon" },
        { name: "Physics", code: "9702", papers: ["Paper 1 (MCQ)", "Paper 2 (AS Structured)", "Paper 4 (A Level)", "Paper 5 (Practical)"], status: "Coming Soon" },
        { name: "Chemistry", code: "9701", papers: ["Paper 1 (MCQ)", "Paper 2 (AS Structured)", "Paper 4 (A Level)", "Paper 5 (Practical)"], status: "Coming Soon" },
        { name: "Biology", code: "9700", papers: ["Paper 1 (MCQ)", "Paper 2 (AS Structured)", "Paper 4 (A Level)", "Paper 5 (Practical)"], status: "Coming Soon" },
        { name: "Economics", code: "9708", papers: ["Paper 1 (MCQ)", "Paper 2 (Data Response)", "Paper 3 (Multiple Choice)", "Paper 4 (Essays)"], status: "Coming Soon" },
        { name: "Accounting", code: "9706", papers: ["Paper 1 (MCQ)", "Paper 2 (Structured)", "Paper 3 (A Level)"], status: "Coming Soon" },
      ]
    }
  ];

  const levels = activeBoard === "zimsec" ? zimsecLevels : cambridgeLevels;

  return (
    <div className="flex flex-col min-h-screen pt-24 md:pt-32">
      <main className="flex-1">
        <section className="px-6 pb-16">
          <div className="max-w-4xl mx-auto text-center mb-12">
            <h1 className="text-calm-h1 mb-6 text-foreground">Subjects & Coverage</h1>
            <p className="text-calm-body max-w-2xl mx-auto mb-8">
              Full coverage for both ZIMSEC and Cambridge exam boards.
            </p>
            {/* Board toggle */}
            <div className="inline-flex rounded-full border border-border bg-zinc-50 p-1 gap-1">
              <button
                onClick={() => setActiveBoard("zimsec")}
                className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${activeBoard === "zimsec" ? "bg-white shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                🇿🇼 ZIMSEC
              </button>
              <button
                onClick={() => setActiveBoard("cambridge")}
                className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${activeBoard === "cambridge" ? "bg-white shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                🎓 Cambridge
              </button>
            </div>
          </div>

          <div className="max-w-4xl mx-auto space-y-16">
            {levels.map((level, levelIndex) => (
              <div key={levelIndex}>
                <div className="flex items-center gap-3 mb-8 border-b border-border pb-4">
                  <div className="p-2 bg-zinc-100 rounded-lg">
                    {level.icon}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">{level.title}</h2>
                    <p className="text-sm text-muted-foreground">{level.description}</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  {level.subjects.map((sub, i) => (
                    <div key={i} className="bg-card border border-border rounded-2xl p-6 flex flex-col hover:border-primary/30 transition-colors">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="font-bold text-lg">{sub.name}</h3>
                            <p className="text-xs text-muted-foreground font-mono">{sub.code}</p>
                        </div>
                        {sub.status === "Available" ? (
                            <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
                                Available
                            </span>
                        ) : (
                            <span className="bg-zinc-100 text-zinc-500 text-xs font-bold px-2 py-1 rounded-full">
                                Coming Soon
                            </span>
                        )}
                      </div>
                      
                      <div className="space-y-2 mt-2">
                          <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Papers Covered</p>
                          <ul className="space-y-1">
                              {sub.papers.map((paper, j) => (
                                  <li key={j} className="text-sm text-zinc-700 flex items-center gap-2">
                                      <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full" />
                                      {paper}
                                  </li>
                              ))}
                          </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          
          <div className="max-w-3xl mx-auto mt-20 p-6 bg-blue-50 border border-blue-100 rounded-xl flex items-start gap-4">
              <CheckCircle2 className="w-6 h-6 text-blue-600 shrink-0 mt-1" />
              <div>
                  <h4 className="font-bold text-blue-900 mb-1">Aligned to Official Syllabuses</h4>
                  <p className="text-sm text-blue-800/80 leading-relaxed">
                    {activeBoard === "zimsec"
                      ? "All ZIMSEC content is strictly aligned to the latest Zimbabwe School Examinations Council curriculum. Everything is tailored for the Zimbabwean student — no generic international content."
                      : "All Cambridge content is aligned to the latest Cambridge Assessment International Education (CAIE) syllabuses. Papers and marking follow Cambridge examiner standards."
                    }
                  </p>
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
