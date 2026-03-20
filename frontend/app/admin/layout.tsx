"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useUserIdentity } from "@/lib/identity/useUserIdentity";
import { LoadingState } from "@/components/system/LoadingState";
import { logout } from "@/lib/auth";
import {
  LayoutDashboard,
  FileText,
  Upload,
  BookOpen,
  LogOut,
  ChevronRight,
} from "lucide-react";

const NAV = [
  { label: "Overview", href: "/admin", icon: LayoutDashboard, exact: true },
  { label: "Papers", href: "/admin/papers", icon: FileText },
  { label: "Upload Paper", href: "/admin/papers/upload", icon: Upload },
  { label: "Syllabus", href: "/admin/syllabus", icon: BookOpen },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { identity, isLoading } = useUserIdentity();

  useEffect(() => {
    if (!isLoading && !identity) router.replace("/login");
    if (!isLoading && identity && identity.role !== "ADMIN") router.replace("/dashboard");
  }, [identity, isLoading, router]);

  if (isLoading || !identity) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingState variant="spinner" text="Loading..." />
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen flex bg-zinc-50">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-white border-r border-zinc-200 flex flex-col">
        <div className="h-16 px-6 flex items-center border-b border-zinc-200">
          <span className="font-bold text-lg text-zinc-900">ZimPrep</span>
          <span className="ml-2 text-[10px] font-semibold uppercase tracking-widest bg-zinc-900 text-white px-1.5 py-0.5 rounded">
            Admin
          </span>
        </div>

        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map((item) => {
            const Icon = item.icon;
            const active = item.exact
              ? pathname === item.href
              : pathname === item.href || (item.href !== "/admin" && pathname.startsWith(item.href + "/"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  active ? "bg-zinc-900 text-white" : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-zinc-200">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-zinc-600 hover:bg-red-50 hover:text-red-600 w-full transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-zinc-200 px-8 flex items-center gap-2 text-sm text-zinc-500">
          <span>Admin</span>
          {pathname !== "/admin" && (
            <>
              <ChevronRight className="w-3 h-3" />
              <span className="text-zinc-900 font-medium capitalize">
                {pathname.split("/").filter(Boolean).slice(1).join(" / ")}
              </span>
            </>
          )}
        </header>

        <main className="flex-1 p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
