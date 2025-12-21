"use client";

import { RoleGuard } from "@/components/system/RoleGuard";
import { ReactNode } from "react";

/**
 * Layout for parent routes.
 * All routes under /parent require PARENT role.
 */
export default function ParentLayout({ children }: { children: ReactNode }) {
  return (
    <RoleGuard allowedRoles={["PARENT"]}>
      {children}
    </RoleGuard>
  );
}
