"use client";

import Link from "next/link";
import Image from "next/image";
import { BookOpen, PenTool, Zap, Hexagon } from "lucide-react";
import "@/app/animations.css";

interface AuthLayoutProps {
  children: React.ReactNode;
  heading: string;
  subheading?: string;
}

export function AuthLayout({ children, heading, subheading }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-zinc-50/50 p-4 relative overflow-hidden">
      
      {/* 
        PREMIUM ANIMATED OBJECTS 
        Abstract 3D-like shapes and academic icons floating in 3D space
      */}
      
      {/* 1. Large Glassy Orb (Top Left) */}
      <div className="absolute top-[-10%] left-[-5%] w-96 h-96 bg-gradient-to-br from-primary/20 to-emerald-300/20 rounded-full blur-3xl animate-float opacity-60" />

      {/* 2. Floating Book Icon (Left) */}
      <div className="absolute top-[20%] left-[10%] hidden lg:block animate-float-delayed">
        <div className="bg-white p-4 rounded-2xl shadow-xl shadow-emerald-900/5 rotate-[-12deg] border border-white/40 backdrop-blur-sm">
            <BookOpen className="w-8 h-8 text-primary" />
        </div>
      </div>

      {/* 3. Floating Pen Icon (Right) */}
      <div className="absolute bottom-[20%] right-[10%] hidden lg:block animate-float">
        <div className="bg-white p-4 rounded-2xl shadow-xl shadow-emerald-900/5 rotate-[12deg] border border-white/40 backdrop-blur-sm">
            <PenTool className="w-8 h-8 text-emerald-600" />
        </div>
      </div>

      {/* 4. Abstract Cube/Hexagon (Top Right) */}
      <div className="absolute top-[15%] right-[15%] hidden md:block animate-float-slow">
         <div className="relative group">
            <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full" />
            <Hexagon className="w-16 h-16 text-emerald-200/50 rotate-12" strokeWidth={1} />
         </div>
      </div>

      {/* 5. Zap/Energy Icon (Bottom Left) */}
      <div className="absolute bottom-[15%] left-[15%] hidden md:block animate-float-reverse">
         <div className="bg-gradient-to-br from-amber-100 to-amber-50 p-3 rounded-xl shadow-lg shadow-amber-900/5 -rotate-6 border border-white/60">
            <Zap className="w-6 h-6 text-amber-500 fill-amber-500" />
         </div>
      </div>

      {/* 6. REAL 3D CHARACTERS */}
      {/* Female Student (Left) */}
      <div className="absolute bottom-[5%] left-[5%] xl:left-[10%] hidden xl:block animate-float-slow w-64 h-64 pointer-events-none select-none z-0 opacity-80 mix-blend-multiply">
          <Image 
            src="/images/student_female.png" 
            alt="Student learning" 
            width={512} 
            height={512} 
            className="w-full h-full object-contain drop-shadow-2xl"
          />
      </div>

      {/* Male Student (Right) */}
      <div className="absolute top-[10%] right-[5%] xl:right-[8%] hidden xl:block animate-float w-72 h-72 pointer-events-none select-none z-0 opacity-80 mix-blend-multiply">
          <Image 
            src="/images/student_male.png" 
            alt="Student reading" 
            width={512} 
            height={512} 
            className="w-full h-full object-contain drop-shadow-2xl"
          />
      </div>


      {/* Main Content Card */}
      <div className="w-full max-w-md space-y-8 relative z-10 animate-fade-in perspective-1000">
        <div className="text-center space-y-2 animate-slide-up">
            <Link href="/" className="inline-block hover:scale-105 transition-transform duration-300">
                 <h1 className="text-3xl font-bold tracking-tight text-primary drop-shadow-sm">ZimPrep</h1>
            </Link>
          <h2 className="text-calm-h3 text-foreground mt-4">{heading}</h2>
          {subheading && (
            <p className="text-calm-body text-base text-muted-foreground animate-stagger-1">
              {subheading}
            </p>
          )}
        </div>
        
        {/* Glass Card */}
        <div className="bg-white/80 backdrop-blur-xl border border-white/50 p-8 rounded-[2.5rem] shadow-2xl shadow-zinc-200/50 hover:shadow-zinc-200/80 transition-all duration-500 animate-scale-in hover:translate-y-[-4px]">
            {children}
        </div>
        
        <div className="text-center text-sm text-muted-foreground opacity-60 animate-stagger-2">
             <p>&copy; 2025 ZimPrep. Secure & Private.</p>
        </div>
      </div>
    </div>
  );
}
