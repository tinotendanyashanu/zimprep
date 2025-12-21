"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useUserIdentity } from "@/lib/identity/useUserIdentity";
import { canAccessRoute } from "@/lib/identity/roleGuards";
import { Role } from "@/lib/identity/types";
import { AccessDeniedState } from "./AccessDeniedState";
import { LoadingState } from "./LoadingState";

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles?: Role[];
  fallback?: ReactNode;
}

/**
 * Declarative role guard component.
 * Renders children only if the current user's role is allowed.
 * Otherwise renders AccessDeniedState.
 */
export function RoleGuard({ children, allowedRoles, fallback }: RoleGuardProps) {
  const { identity, isLoading } = useUserIdentity();
  const pathname = usePathname();

  // Show loading state while identity is being resolved
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingState variant="spinner" text="Verifying access..." />
      </div>
    );
  }

  // No identity = not authenticated (should redirect to login in real app)
  if (!identity) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <AccessDeniedState
          title="Session Required"
          description="Please sign in to continue."
          action={{
            label: "Sign In",
            onClick: () => (window.location.href = "/login"),
          }}
        />
      </div>
    );
  }

  // Check if role is explicitly allowed
  if (allowedRoles && allowedRoles.length > 0) {
    if (!allowedRoles.includes(identity.role)) {
      return fallback || (
        <div className="min-h-screen flex items-center justify-center p-8">
          <AccessDeniedState
            description="This section is not available for your account type."
          />
        </div>
      );
    }
  }

  // Check route access based on role
  if (!canAccessRoute(identity.role, pathname)) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center p-8">
        <AccessDeniedState
          description="This section is not available for your account type."
        />
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * HOC variant for wrapping entire pages.
 */
export function withRoleGuard<P extends object>(
  Component: React.ComponentType<P>,
  allowedRoles?: Role[]
) {
  return function GuardedComponent(props: P) {
    return (
      <RoleGuard allowedRoles={allowedRoles}>
        <Component {...props} />
      </RoleGuard>
    );
  };
}
