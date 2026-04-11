import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * GET /api/auth/role
 *
 * Validates the caller's Supabase JWT and returns their role.
 * Uses the service-role key server-side so it bypasses RLS and works
 * even when the Python backend is unreachable (e.g. on Vercel).
 *
 * Response shapes:
 *   { role: "admin",    id, name, email }   — admin employee
 *   { role: "employee", id, name, email }   — regular employee
 *   { role: "parent" }                      — parent account
 *   { role: "student" }                     — default / student
 *
 * Requires env vars (server-side, no NEXT_PUBLIC_ prefix):
 *   SUPABASE_SERVICE_ROLE_KEY
 */
export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return NextResponse.json({ error: "Missing bearer token" }, { status: 401 });
  }
  const token = authHeader.slice(7);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!serviceKey) {
    return NextResponse.json(
      { error: "SUPABASE_SERVICE_ROLE_KEY is not configured on this server" },
      { status: 500 }
    );
  }

  // Service-role client — bypasses RLS
  const sb = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false },
  });

  // Validate the JWT and get the user
  const { data: userData, error: userError } = await sb.auth.getUser(token);
  if (userError || !userData.user) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 401 });
  }
  const user = userData.user;

  // 1. Check employee table by user_id (fast path)
  let emp: { id: string; name: string; role: string; email: string; is_active: boolean; user_id: string | null } | null = null;

  const { data: empById } = await sb
    .from("employee")
    .select("id, name, role, email, is_active, user_id")
    .eq("user_id", user.id)
    .maybeSingle();

  emp = empById;

  // 2. Fallback: look up by email (invited but user_id not yet linked)
  if (!emp && user.email) {
    const { data: empByEmail } = await sb
      .from("employee")
      .select("id, name, role, email, is_active, user_id")
      .eq("email", user.email)
      .maybeSingle();

    if (empByEmail) {
      emp = empByEmail;
      // Link the user_id so future lookups are fast
      if (!emp.user_id) {
        await sb.from("employee").update({ user_id: user.id }).eq("id", emp.id);
      }
    }
  }

  if (emp && emp.is_active) {
    return NextResponse.json({
      role: emp.role,   // "admin" | "employee"
      id: emp.id,
      name: emp.name,
      email: emp.email,
    });
  }

  // 3. Check parent table
  const { data: parent } = await sb
    .from("parent")
    .select("id")
    .eq("id", user.id)
    .maybeSingle();

  if (parent) {
    return NextResponse.json({ role: "parent" });
  }

  // 4. Default: student
  return NextResponse.json({ role: "student" });
}
