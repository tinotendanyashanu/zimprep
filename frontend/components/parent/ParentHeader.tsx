import React from 'react';
import Link from 'next/link';
import { Shield, UserCircle, Bell } from 'lucide-react';
import { Button } from "@/components/ui/button";

export function ParentHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-black/80 backdrop-blur-xl">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        
        {/* Branding */}
        <div className="flex items-center gap-2">
            <div className="bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded-xl">
                <Shield className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />
            </div>
            <span className="font-bold tracking-tight text-lg text-zinc-900 dark:text-zinc-100">
                ZimPrep <span className="text-zinc-500 font-medium">Guardian</span>
            </span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
             <Button variant="ghost" size="icon" className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 dark:hover:bg-zinc-800 rounded-full">
                <Bell className="w-5 h-5" />
             </Button>
             
             <div className="h-6 w-px bg-zinc-200 dark:bg-zinc-800 mx-1" />

             <Link href="/parent/profile">
                <Button variant="ghost" className="pl-2 pr-4 gap-2 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800">
                    <div className="w-8 h-8 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center">
                        <UserCircle className="w-5 h-5 text-zinc-600 dark:text-zinc-400" />
                    </div>
                    <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300 hidden sm:inline-block">Profile</span>
                </Button>
             </Link>
        </div>

      </div>
    </header>
  );
}
