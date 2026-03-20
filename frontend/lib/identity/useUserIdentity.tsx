"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { UserIdentity, Role } from "./types";
import { supabase } from "@/lib/supabase";

interface IdentityContextValue {
  identity: UserIdentity | null;
  isLoading: boolean;
}

const IdentityContext = createContext<IdentityContextValue | undefined>(undefined);

function roleToPermissions(role: Role): string[] {
  switch (role) {
    case "ADMIN":    return ["audit", "manage_content", "practice", "view_results", "view_history"];
    case "PARENT":   return ["view_progress"];
    case "EXAMINER": return ["manage_content"];
    default:         return ["practice", "view_results", "view_history"];
  }
}

function buildIdentity(user: { id: string; user_metadata?: Record<string, unknown> }): UserIdentity {
  const rawRole = (user.user_metadata?.role as string | undefined)?.toUpperCase() as Role | undefined;
  const role: Role = rawRole && ["STUDENT", "PARENT", "ADMIN", "EXAMINER"].includes(rawRole)
    ? rawRole
    : "STUDENT";
  return {
    user_id: user.id,
    role,
    linked_student_id: user.user_metadata?.linked_student_id as string | undefined,
    permissions: roleToPermissions(role),
  };
}

export function IdentityProvider({ children }: { children: ReactNode }) {
  const [identity, setIdentity] = useState<UserIdentity | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setIdentity(buildIdentity(user));
      setIsLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setIdentity(session?.user ? buildIdentity(session.user) : null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <IdentityContext.Provider value={{ identity, isLoading }}>
      {children}
    </IdentityContext.Provider>
  );
}

export function useUserIdentity(): IdentityContextValue {
  const ctx = useContext(IdentityContext);
  if (!ctx) throw new Error("useUserIdentity must be used within IdentityProvider");
  return ctx;
}
