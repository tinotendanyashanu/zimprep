import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * GET /api/auth/role
 *
 * Validates the caller's Supabase JWT and returns their highest-priority role.
 * Role priority: admin > employee > parent > student.
 *
 * Primary source: user_roles table (new RBAC schema).
 * Fallback:       employee table (backward-compat for existing records).
 *
 * Response shapes:
 *   { role: "admin",    id, name, email }
 *   { role: "employee", id, name, email }
 *   { role: "parent",   id }
 *   { role: "student"              }   ← default
 */
export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return NextResponse.json({ error: "Missing bearer token" }, { status: 401 });
  }
  const token = authHeader.slice(7);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const serviceKey  = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!serviceKey) {
    return NextResponse.json(
      { error: "SUPABASE_SERVICE_ROLE_KEY is not configured" },
      { status: 500 }
    );
  }

  // Service-role client — bypasses RLS
  const sb = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false },
  });

  // Validate the JWT
  const { data: userData, error: userError } = await sb.auth.getUser(token);
  if (userError || !userData.user) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 401 });
  }
  const user = userData.user;

  // ── 1. Check user_roles (new RBAC table) ─────────────────────────────────
  const { data: roleRows } = await sb
    .from("user_roles")
    .select("roles(name)")
    .eq("user_id", user.id);

  const roles: string[] = (roleRows ?? [])
    .flatMap((r: { roles: { name: string }[] | { name: string } | null }) =>
      Array.isArray(r.roles) ? r.roles.map((x) => x.name) : r.roles ? [r.roles.name] : []
    )
    .filter(Boolean);

  if (roles.includes("admin") || roles.includes("employee")) {
    // Fetch profile from employee table for name/email
    const { data: emp } = await sb
      .from("employee")
      .select("id, name, role, email, is_active")
      .eq("user_id", user.id)
      .maybeSingle();

    const resolvedRole = roles.includes("admin") ? "admin" : "employee";
    return NextResponse.json({
      role:  emp?.role ?? resolvedRole,
      id:    emp?.id   ?? user.id,
      name:  emp?.name ?? user.email ?? "",
      email: emp?.email ?? user.email ?? "",
    });
  }

  if (roles.includes("parent")) {
    return NextResponse.json({ role: "parent", id: user.id });
  }

  if (roles.includes("student")) {
    return NextResponse.json({ role: "student" });
  }

  // ── 2. Fallback: legacy employee table (for accounts created before 019) ──
  let emp: {
    id: string; name: string; role: string;
    email: string; is_active: boolean; user_id: string | null;
  } | null = null;

  const { data: empById } = await sb
    .from("employee")
    .select("id, name, role, email, is_active, user_id")
    .eq("user_id", user.id)
    .maybeSingle();
  emp = empById;

  if (!emp && user.email) {
    const { data: empByEmail } = await sb
      .from("employee")
      .select("id, name, role, email, is_active, user_id")
      .eq("email", user.email)
      .maybeSingle();

    if (empByEmail) {
      emp = empByEmail;
      if (!emp.user_id) {
        await sb.from("employee").update({ user_id: user.id }).eq("id", emp.id);
      }
    }
  }

  if (emp && emp.is_active) {
    return NextResponse.json({
      role:  emp.role,
      id:    emp.id,
      name:  emp.name,
      email: emp.email,
    });
  }

  // ── 3. Fallback: legacy parent table ──────────────────────────────────────
  const { data: parent } = await sb
    .from("parent")
    .select("id")
    .eq("id", user.id)
    .maybeSingle();

  if (parent) {
    return NextResponse.json({ role: "parent", id: user.id });
  }

  // ── 4. Default: student ───────────────────────────────────────────────────
  return NextResponse.json({ role: "student" });
}
