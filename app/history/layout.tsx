"use client";

import { RoleGuard } from "@/components/system/RoleGuard";
import { ReactNode } from "react";

/**
 * Layout for history routes.
 * All routes under /history require STUDENT role.
 */
export default function HistoryLayout({ children }: { children: ReactNode }) {
  return (
    <RoleGuard allowedRoles={["STUDENT"]}>
      {children}
    </RoleGuard>
  );
}
