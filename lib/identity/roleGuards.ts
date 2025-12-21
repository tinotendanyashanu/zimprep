import { Role, ROLE_ROUTE_ACCESS } from "./types";

/**
 * Check if a role can access a given route.
 */
export function canAccessRoute(role: Role, pathname: string): boolean {
  const allowedPrefixes = ROLE_ROUTE_ACCESS[role] || [];
  return allowedPrefixes.some((prefix) => pathname.startsWith(prefix));
}

/**
 * Get the list of accessible routes for a role.
 */
export function getAccessibleRoutes(role: Role): string[] {
  return ROLE_ROUTE_ACCESS[role] || [];
}

/**
 * Check if a role has a specific permission.
 * Future-proofed for granular backend permissions.
 */
export function hasPermission(permissions: string[], requiredPermission: string): boolean {
  return permissions.includes(requiredPermission);
}

/**
 * Role hierarchy helpers (if needed in future).
 * Currently all roles are equal with no inheritance.
 */
export function isStudentRole(role: Role): boolean {
  return role === "STUDENT";
}

export function isParentRole(role: Role): boolean {
  return role === "PARENT";
}

export function isAdminRole(role: Role): boolean {
  return role === "ADMIN";
}

export function isExaminerRole(role: Role): boolean {
  return role === "EXAMINER";
}
