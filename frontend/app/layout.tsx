import type { Metadata, Viewport } from "next";
import { DM_Sans, Inter } from "next/font/google";
import "katex/dist/katex.min.css";
import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ZimPrep | Master the Art of Exams",
  description: "Experience the most cinematic and effective ZIMSEC preparation platform. Master examiner techniques with data-driven insights.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light scroll-smooth max-w-full overflow-x-hidden" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${dmSans.variable} antialiased font-sans bg-background text-foreground selection:bg-primary/20 selection:text-primary-foreground max-w-full overflow-x-hidden`}
        suppressHydrationWarning
      >
        <main className="relative min-h-screen max-w-full overflow-x-hidden">{children}</main>
      </body>
    </html>
  );
}
