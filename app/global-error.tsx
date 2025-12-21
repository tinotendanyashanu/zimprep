"use client";

import { ErrorState } from "@/components/system/ErrorState";
import "@/app/globals.css";
import { DM_Sans } from "next/font/google";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className={`${dmSans.variable} antialiased font-sans bg-background text-foreground`}>
        <div className="min-h-screen flex items-center justify-center p-4">
          <ErrorState
            title="System Error"
            message="We encountered an unexpected problem. Our team has been notified."
            retryAction={reset}
          />
        </div>
      </body>
    </html>
  );
}
