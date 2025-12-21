"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { UserIdentity, Role } from "./types";

const MOCK_IDENTITIES: Record<string, UserIdentity> = {
  student: {
    user_id: "student_001",
    role: "STUDENT",
    permissions: ["practice", "view_results", "view_history"],
  },
  parent: {
    user_id: "parent_001",
    role: "PARENT",
    linked_student_id: "student_001",
    permissions: ["view_progress"],
  },
  admin: {
    user_id: "admin_001",
    role: "ADMIN",
    permissions: ["audit", "manage_content"],
  },
};

interface IdentityContextValue {
  identity: UserIdentity | null;
  isLoading: boolean;
  setMockRole: (role: Role) => void;
}

const IdentityContext = createContext<IdentityContextValue | undefined>(undefined);

export function IdentityProvider({ children }: { children: ReactNode }) {
  const [identity, setIdentity] = useState<UserIdentity | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedRole = localStorage.getItem("mock_role") as Role | null;
    const role = storedRole || "STUDENT";
    const mockKey = role.toLowerCase();
    const mockIdentity = MOCK_IDENTITIES[mockKey] || MOCK_IDENTITIES.student;
    setIdentity(mockIdentity);
    setIsLoading(false);
  }, []);

  const setMockRole = (role: Role) => {
    localStorage.setItem("mock_role", role);
    const mockKey = role.toLowerCase();
    setIdentity(MOCK_IDENTITIES[mockKey] || MOCK_IDENTITIES.student);
  };

  return (
    <IdentityContext.Provider value={{ identity, isLoading, setMockRole }}>
      {children}
    </IdentityContext.Provider>
  );
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
