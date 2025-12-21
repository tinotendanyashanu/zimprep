"use client";

import { RoleGuard } from "@/components/system/RoleGuard";
import { ReactNode } from "react";

/**
 * Layout for student dashboard routes.
 * All routes under /dashboard require STUDENT role.
 */
export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <RoleGuard allowedRoles={["STUDENT"]}>
      {children}
    </RoleGuard>
  );
}
