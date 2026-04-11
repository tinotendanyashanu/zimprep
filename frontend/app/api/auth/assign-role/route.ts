import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * POST /api/auth/assign-role
 *
 * Assigns a role to the authenticated user in the user_roles table.
 * Uses the service-role key to bypass RLS — only called from trusted
 * server-side flows (student/parent registration, employee invite).
 *
 * Allowed public roles: "student" | "parent"
 * Admin/employee roles are assigned via the backend invite flow only.
 *
 * Body: { role: "student" | "parent" }
 * Auth: Bearer <access_token>
 */
export async function POST(request: Request) {
  const authHeader = request.headers.get("authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return NextResponse.json({ error: "Missing bearer token" }, { status: 401 });
  }
  const token = authHeader.slice(7);

  const body = await request.json().catch(() => ({}));
  const { role } = body as { role?: string };

  if (!role || !["student", "parent"].includes(role)) {
    return NextResponse.json({ error: "Invalid role. Must be 'student' or 'parent'" }, { status: 400 });
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const serviceKey  = process.env.SUPABASE_SERVICE_ROLE_KEY!;

  const sb = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false },
  });

  // Validate the JWT
  const { data: userData, error: userError } = await sb.auth.getUser(token);
  if (userError || !userData.user) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 401 });
  }
  const userId = userData.user.id;

  // Look up role id
  const { data: roleRow } = await sb
    .from("roles")
    .select("id")
    .eq("name", role)
    .single();

  if (!roleRow) {
    return NextResponse.json({ error: "Role not found in database" }, { status: 500 });
  }

  // Insert into user_roles (upsert — safe to call multiple times)
  const { error: insertError } = await sb
    .from("user_roles")
    .upsert({ user_id: userId, role_id: roleRow.id }, { onConflict: "user_id,role_id" });

  if (insertError) {
    return NextResponse.json({ error: insertError.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true, role });
}
