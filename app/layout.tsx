import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { SessionRecoveryNotice } from "@/components/system/SessionRecoveryNotice";
import { IdentityProvider } from "@/lib/identity/useUserIdentity";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ZimPrep | Master the Art of Exams",
  description: "Experience the most cinematic and effective ZIMSEC preparation platform. Master examiner techniques with data-driven insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light scroll-smooth" suppressHydrationWarning>
      <body
        className={`${dmSans.variable} antialiased font-sans bg-background text-foreground selection:bg-primary/20 selection:text-primary-foreground`}
        suppressHydrationWarning
      >
        <IdentityProvider>
          <main className="relative">
            {children}
            <SessionRecoveryNotice />
          </main>
        </IdentityProvider>
      </body>
    </html>
  );
}

