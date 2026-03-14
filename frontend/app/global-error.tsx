"use client";

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
      <body
        className={`${dmSans.variable} antialiased font-sans bg-background text-foreground`}
      >
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="text-center max-w-md">
            <h1 className="text-xl font-semibold text-foreground mb-2">
              Something went wrong
            </h1>
            <p className="text-muted-foreground text-sm mb-6">
              {error.message ?? "An unexpected error occurred."}
            </p>
            <button
              onClick={reset}
              className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:opacity-90 transition"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
