/**
 * Identity Types for ZimPrep
 * Locked contract - do not modify without backend alignment.
 */

export type Role = "STUDENT" | "PARENT" | "ADMIN" | "EXAMINER";

export interface UserIdentity {
  user_id: string;
  role: Role;
  linked_student_id?: string; // For parents viewing a student
  permissions: string[]; // Future-proofed for granular permissions
}

/**
 * Route access rules per role.
 * Define which route prefixes each role can access.
 */
export const ROLE_ROUTE_ACCESS: Record<Role, string[]> = {
  STUDENT: ["/dashboard", "/exam", "/history", "/subjects", "/subscription", "/results", "/recommendations"],
  PARENT: ["/parent"],
  ADMIN: ["/admin"],
  EXAMINER: ["/examiner"],
};

/**
 * Default redirect per role when accessing the app root.
 */
export const ROLE_DEFAULT_ROUTE: Record<Role, string> = {
  STUDENT: "/dashboard",
  PARENT: "/parent",
  ADMIN: "/admin",
  EXAMINER: "/examiner",
};
