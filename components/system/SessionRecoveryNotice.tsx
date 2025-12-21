"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// This component simulates session monitoring and displays alerts
// In a real app, this would hook into auth state/network listeners
export function SessionRecoveryNotice() {
  const [isOffline, setIsOffline] = useState(false);
  
  // Example monitoring - in a real app this would be more robust
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] max-w-md animate-in slide-in-from-bottom-4 fade-in">
      <div className="flex items-center gap-4 p-4 rounded-lg border border-warning/50 bg-background shadow-lg">
        <div className="flex-shrink-0">
          <WifiOff className="h-5 w-5 text-warning" />
        </div>
        <div className="flex-1">
          <h4 className="text-sm font-medium">Connection Lost</h4>
          <p className="text-xs text-muted-foreground mt-1">
            Reconnecting found... Your progress is saved locally.
          </p>
        </div>
      </div>
    </div>
  );
}
