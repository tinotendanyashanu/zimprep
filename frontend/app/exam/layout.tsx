"use client";

import { RoleGuard } from "@/components/system/RoleGuard";
import { ReactNode } from "react";

/**
 * Layout for exam routes.
 * All routes under /exam require STUDENT role.
 */
export default function ExamLayout({ children }: { children: ReactNode }) {
  return (
    <RoleGuard allowedRoles={["STUDENT"]}>
      {children}
    </RoleGuard>
  );
}
