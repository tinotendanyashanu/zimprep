"use client";

import { Button } from "@/components/ui/button";
import { LogOut, User, History, CreditCard, BookOpen, Home, Shield } from "lucide-react";
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
  { label: "Dashboard", href: "/dashboard", icon: Home, roles: ["STUDENT"] },
  { label: "History", href: "/history", icon: History, roles: ["STUDENT"] },
  { label: "Subscription", href: "/subscription", icon: CreditCard, roles: ["STUDENT"] },
  { label: "Admin Panel", href: "/admin", icon: Shield, roles: ["ADMIN"] },
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
    return item.roles ? item.roles.includes(identity.role) : canAccessRoute(identity.role, item.href);
  });

  return (
    <header className="h-20 border-b-4 border-border bg-card px-6 flex items-center justify-between sticky top-0 z-50 shadow-sm">
      <div className="flex items-center gap-8">
        <div className="font-extrabold text-2xl tracking-tight text-primary flex items-center gap-2">
           <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center rotate-3">
             <BookOpen className="w-5 h-5 text-white -rotate-3" />
           </div>
           {title}
        </div>
        
        {/* Role-aware navigation */}
        <nav className="hidden md:flex items-center gap-4 ml-6">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold uppercase tracking-wide transition-all border-2",
                  isActive 
                    ? "bg-primary/10 text-primary border-primary/20 shadow-sm" 
                    : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/50 hover:border-border"
                )}
              >
                <Icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-muted-foreground")} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Role indicator (dev only) */}
        {identity && (
          <span className="hidden sm:inline-flex text-[10px] font-black uppercase tracking-wider text-muted-foreground bg-muted border-2 border-border px-3 py-1.5 rounded-xl">
            {identity.role}
          </span>
        )}
        <div className="w-10 h-10 rounded-2xl bg-secondary flex items-center justify-center text-xs font-bold text-foreground border-2 border-border shadow-sm">
           <User className="w-5 h-5" />
        </div>
        <Button variant="ghost" size="icon" className="rounded-xl border-2 border-transparent hover:border-red-200 hover:bg-red-50 hover:text-red-500 text-muted-foreground" onClick={handleLogout} title="Logout">
          <LogOut className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}

