import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import NavBar from "./NavBar";

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
      >
        <NavBar />
        <main className="relative">{children}</main>
      </body>
    </html>
  );
}
