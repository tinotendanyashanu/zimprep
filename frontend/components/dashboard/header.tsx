"use client";

import { Button } from "@/components/ui/button";
import { LogOut, User, History, CreditCard, BookOpen, Home } from "lucide-react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useUserIdentity } from "@/lib/identity/useUserIdentity";
import { canAccessRoute } from "@/lib/identity/roleGuards";
import { cn } from "@/lib/utils";

interface DashboardHeaderProps {
    title?: React.ReactNode;
}

// Navigation items with their required routes for visibility check
const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: Home },
  { label: "History", href: "/history", icon: History },
  { label: "Subscription", href: "/subscription", icon: CreditCard },
];

export function DashboardHeader({ title = "ZimPrep" }: DashboardHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { identity } = useUserIdentity();

  const handleLogout = () => {
    localStorage.clear();
    router.replace("/");
  };

  // Filter nav items based on role
  const visibleNavItems = NAV_ITEMS.filter((item) => {
    if (!identity) return false;
    return canAccessRoute(identity.role, item.href);
  });

  return (
    <header className="h-16 border-b border-zinc-200 bg-white/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-8">
        <div className="font-bold text-xl text-primary">{title}</div>
        
        {/* Role-aware navigation */}
        <nav className="hidden md:flex items-center gap-1">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-zinc-100 text-zinc-900" 
                    : "text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50"
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Role indicator (dev only) */}
        {identity && (
          <span className="hidden sm:inline-flex text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded">
            {identity.role}
          </span>
        )}
        <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center text-xs font-bold text-zinc-500 border border-zinc-200">
           <User className="w-4 h-4" />
        </div>
        <Button variant="ghost" size="icon" onClick={handleLogout} title="Logout">
          <LogOut className="w-4 h-4 text-muted-foreground hover:text-red-500" />
        </Button>
      </div>
    </header>
  );
}

