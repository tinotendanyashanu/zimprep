"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { UserIdentity, Role } from "./types";
import { getUser, User } from "@/lib/auth";

const IdentityContext = createContext<IdentityContextValue | undefined>(
  undefined,
);

interface IdentityContextValue {
  identity: UserIdentity | null;
  isLoading: boolean;
  setMockRole: (role: Role) => void; // Kept for interface compatibility but warns logs
}

export function IdentityProvider({ children }: { children: ReactNode }) {
  const [identity, setIdentity] = useState<UserIdentity | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Sync identity with real auth state
  useEffect(() => {
    const loadIdentity = () => {
      const user = getUser();
      if (user) {
        setIdentity({
          user_id: user.id,
          role: (user.role as Role) || "STUDENT",
          permissions: derivePermissions(user.role || "STUDENT"),
        });
      } else {
        setIdentity(null);
      }
      setIsLoading(false);
    };

    // Initial load
    loadIdentity();

    // Optional: Listen for storage events (logout in other tabs)
    window.addEventListener("storage", loadIdentity);
    return () => window.removeEventListener("storage", loadIdentity);
  }, []);

  const setMockRole = (role: Role) => {
    console.warn(
      "setMockRole is deprecated. Identity is now driven by real auth.",
    );
  };

  return (
    <IdentityContext.Provider value={{ identity, isLoading, setMockRole }}>
      {children}
    </IdentityContext.Provider>
  );
}

// Helper to map roles to permissions
function derivePermissions(role: string): string[] {
  const normalizedRole = role.toUpperCase();
  if (normalizedRole === "ADMIN") return ["audit", "manage_content"];
  if (normalizedRole === "PARENT") return ["view_progress"];
  return ["practice", "view_results", "view_history"]; // Student default
}

export function useUserIdentity(): IdentityContextValue {
  const context = useContext(IdentityContext);
  if (!context) {
    return {
      identity: null,
      isLoading: true,
      setMockRole: () => {},
    };
  }
  return context;
}

export function useIsStudent(): boolean {
  const { identity } = useUserIdentity();
  return identity?.role === "STUDENT";
}

export function useIsParent(): boolean {
  const { identity } = useUserIdentity();
  return identity?.role === "PARENT";
}

export function useIsAdmin(): boolean {
  const { identity } = useUserIdentity();
  return identity?.role === "ADMIN";
}
