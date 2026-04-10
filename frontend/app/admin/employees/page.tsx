"use client";

import { useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Employee = {
  id: string;
  user_id: string | null;
  email: string;
  name: string;
  role: "admin" | "employee";
  is_active: boolean;
  invited_by: string | null;
  created_at: string;
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-primary/10 text-primary border-primary/20",
  employee: "bg-muted text-muted-foreground border-border",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function RoleBadge({ role }: { role: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border capitalize ${ROLE_COLORS[role] ?? "bg-muted text-muted-foreground border-border"}`}>
      {role}
    </span>
  );
}

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [currentId, setCurrentId] = useState<string>("");

  // Invite
  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: "", name: "", role: "employee" });
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState("");

  // Drawer
  const [selected, setSelected] = useState<Employee | null>(null);
  const [editName, setEditName] = useState("");
  const [editRole, setEditRole] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Search
  const [search, setSearch] = useState("");
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    createClient().auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      const t = session.access_token;
      setToken(t);
      loadEmployees(t);
      fetch(`${BACKEND}/admin/employees/me`, { headers: { Authorization: `Bearer ${t}` } })
        .then((r) => r.json())
        .then((me) => setCurrentId(me.id ?? ""))
        .catch(() => {});
    });
  }, []);

  function loadEmployees(t: string) {
    setLoading(true);
    fetch(`${BACKEND}/admin/employees/`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json())
      .then((data) => setEmployees(Array.isArray(data) ? data : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  function openDrawer(emp: Employee) {
    setSelected(emp);
    setEditName(emp.name);
    setEditRole(emp.role);
    setSaveError("");
    setConfirmDelete(false);
  }

  function closeDrawer() {
    setSelected(null);
    setConfirmDelete(false);
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setInviting(true);
    setInviteError("");
    try {
      const res = await fetch(`${BACKEND}/admin/employees/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(inviteForm),
      });
      if (!res.ok) {
        const err = await res.json();
        setInviteError(err.detail ?? "Failed to invite");
        return;
      }
      setShowInvite(false);
      setInviteForm({ email: "", name: "", role: "employee" });
      loadEmployees(token);
    } finally {
      setInviting(false);
    }
  }

  async function handleSave() {
    if (!token || !selected) return;
    setSaving(true);
    setSaveError("");
    try {
      const res = await fetch(`${BACKEND}/admin/employees/${selected.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name: editName.trim(), role: editRole }),
      });
      if (!res.ok) {
        const err = await res.json();
        setSaveError(err.detail ?? "Failed to save");
        return;
      }
      const updated: Employee = await res.json();
      setEmployees((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      setSelected(updated);
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleActive() {
    if (!token || !selected) return;
    if (selected.is_active) {
      await fetch(`${BACKEND}/admin/employees/${selected.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const updated = { ...selected, is_active: false };
      setEmployees((prev) => prev.map((e) => (e.id === selected.id ? updated : e)));
      setSelected(updated);
    } else {
      const res = await fetch(`${BACKEND}/admin/employees/${selected.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_active: true }),
      });
      const updated: Employee = await res.json();
      setEmployees((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
      setSelected(updated);
    }
  }

  async function handleDelete() {
    if (!token || !selected) return;
    await fetch(`${BACKEND}/admin/employees/${selected.id}/permanent`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    setEmployees((prev) => prev.filter((e) => e.id !== selected.id));
    closeDrawer();
  }

  const filtered = employees.filter((e) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return e.name.toLowerCase().includes(q) || e.email.toLowerCase().includes(q);
  });

  const activeCount = employees.filter((e) => e.is_active).length;
  const pendingCount = employees.filter((e) => e.is_active && !e.user_id).length;
  const isSelf = selected?.id === currentId;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Employees</h1>
          <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
            <span>{employees.length} total</span>
            <span className="text-border">·</span>
            <span className="text-emerald-600 font-medium">{activeCount} active</span>
            {pendingCount > 0 && (
              <>
                <span className="text-border">·</span>
                <span className="text-amber-600 font-medium">{pendingCount} pending signup</span>
              </>
            )}
          </div>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Invite employee
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          type="text"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3.5 py-2 rounded-lg border border-border bg-card text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3 animate-pulse">
            {[...Array(4)].map((_, i) => <div key={i} className="h-10 bg-muted rounded-lg" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2">
            <svg className="w-10 h-10 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
            </svg>
            <p className="text-sm text-muted-foreground">{search ? "No employees match your search" : "No employees yet"}</p>
            {!search && (
              <button onClick={() => setShowInvite(true)} className="text-xs text-primary font-medium hover:underline">
                Invite the first one
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-3 px-4 font-medium">Name</th>
                  <th className="py-3 px-4 font-medium hidden sm:table-cell">Email</th>
                  <th className="py-3 px-4 font-medium">Role</th>
                  <th className="py-3 px-4 font-medium hidden md:table-cell">Joined</th>
                  <th className="py-3 px-4 font-medium">Status</th>
                  <th className="py-3 px-4 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((emp) => (
                  <tr key={emp.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-foreground">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <span className="text-xs font-semibold text-primary">{emp.name[0]?.toUpperCase()}</span>
                        </div>
                        <span className="truncate max-w-[120px]">{emp.name}</span>
                        {emp.id === currentId && (
                          <span className="text-[10px] text-muted-foreground">(you)</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground hidden sm:table-cell truncate max-w-[180px]">{emp.email}</td>
                    <td className="py-3 px-4"><RoleBadge role={emp.role} /></td>
                    <td className="py-3 px-4 text-muted-foreground text-xs hidden md:table-cell">{formatDate(emp.created_at)}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${emp.is_active ? "text-emerald-600" : "text-muted-foreground"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${emp.is_active ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                        {emp.is_active ? "Active" : "Inactive"}
                        {!emp.user_id && emp.is_active && (
                          <span className="ml-1 text-[10px] text-amber-600 font-medium">(pending)</span>
                        )}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => openDrawer(emp)}
                        className="text-xs text-primary font-medium hover:underline"
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Invite modal ─────────────────────────────────────────────────────── */}
      {showInvite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowInvite(false)} />
          <div className="relative z-10 w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl p-6 space-y-5">
            <div>
              <h2 className="text-base font-semibold text-foreground">Invite employee</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                They&apos;ll receive an email with a link to set their password and access the workstation.
              </p>
            </div>
            <form onSubmit={handleInvite} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Full name</label>
                <input
                  required
                  type="text"
                  value={inviteForm.name}
                  onChange={(e) => setInviteForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="Jane Smith"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Email address</label>
                <input
                  required
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm((f) => ({ ...f, email: e.target.value }))}
                  placeholder="jane@example.com"
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Role</label>
                <select
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm((f) => ({ ...f, role: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="employee">Employee — workstation access</option>
                  <option value="admin">Admin — full access</option>
                </select>
              </div>
              {inviteError && <p className="text-xs text-red-500">{inviteError}</p>}
              <div className="flex items-center justify-end gap-3 pt-1">
                <button type="button" onClick={() => setShowInvite(false)} className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted/60 transition">Cancel</button>
                <button type="submit" disabled={inviting} className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-60">
                  {inviting ? "Inviting…" : "Send invite"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Manage drawer ─────────────────────────────────────────────────────── */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={closeDrawer} />
          <div className="relative z-10 w-full max-w-sm h-full bg-card border-l border-border shadow-2xl flex flex-col">
            {/* Drawer header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-semibold text-primary">{selected.name[0]?.toUpperCase()}</span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{selected.name}</p>
                  <p className="text-xs text-muted-foreground">{selected.email}</p>
                </div>
              </div>
              <button onClick={closeDrawer} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted/40 transition text-muted-foreground">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Drawer body */}
            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
              {/* Status info */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  {
                    label: "Status",
                    value: (
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${selected.is_active ? "text-emerald-600" : "text-muted-foreground"}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${selected.is_active ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                        {selected.is_active ? "Active" : "Inactive"}
                      </span>
                    ),
                  },
                  { label: "Joined", value: <span className="text-sm text-foreground">{formatDate(selected.created_at)}</span> },
                  {
                    label: "Account",
                    value: (
                      <span className={`text-xs font-medium ${selected.user_id ? "text-emerald-600" : "text-amber-600"}`}>
                        {selected.user_id ? "Signed up" : "Pending signup"}
                      </span>
                    ),
                  },
                  { label: "Employee ID", value: <span className="text-[10px] font-mono text-muted-foreground break-all">{selected.id.slice(0, 8)}…</span> },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-muted/40 rounded-xl p-3">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
                    <div className="text-sm font-medium text-foreground">{value}</div>
                  </div>
                ))}
              </div>

              {/* Editable fields */}
              <div className="space-y-4">
                <p className="text-xs font-semibold text-foreground uppercase tracking-wide">Edit details</p>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground">Full name</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    disabled={isSelf}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-foreground">Role</label>
                  <select
                    value={editRole}
                    onChange={(e) => setEditRole(e.target.value)}
                    disabled={isSelf}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="employee">Employee</option>
                    <option value="admin">Admin</option>
                  </select>
                  {isSelf && <p className="text-[10px] text-muted-foreground">Cannot edit your own role or name.</p>}
                </div>

                {saveError && <p className="text-xs text-red-500">{saveError}</p>}

                {!isSelf && (
                  <button
                    onClick={handleSave}
                    disabled={saving || (!editName.trim() || (editName === selected.name && editRole === selected.role))}
                    className="w-full py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-50"
                  >
                    {saving ? "Saving…" : "Save changes"}
                  </button>
                )}
              </div>

              {/* Danger zone */}
              {!isSelf && (
                <div className="space-y-3 pt-2">
                  <p className="text-xs font-semibold text-foreground uppercase tracking-wide">Actions</p>
                  <div className="border border-border rounded-xl divide-y divide-border">
                    {/* Toggle active */}
                    <div className="flex items-center justify-between px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {selected.is_active ? "Deactivate account" : "Reactivate account"}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {selected.is_active
                            ? "Blocks login access immediately"
                            : "Restores login access"}
                        </p>
                      </div>
                      <button
                        onClick={handleToggleActive}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          selected.is_active
                            ? "bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200"
                            : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200"
                        }`}
                      >
                        {selected.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                    </div>

                    {/* Permanent delete */}
                    <div className="flex items-center justify-between px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-red-600">Delete permanently</p>
                        <p className="text-xs text-muted-foreground mt-0.5">Removes the record — cannot be undone</p>
                      </div>
                      {!confirmDelete ? (
                        <button
                          onClick={() => setConfirmDelete(true)}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 transition"
                        >
                          Delete
                        </button>
                      ) : (
                        <div className="flex items-center gap-2">
                          <button onClick={() => setConfirmDelete(false)} className="text-xs text-muted-foreground hover:text-foreground">Cancel</button>
                          <button
                            onClick={handleDelete}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-600 text-white hover:bg-red-700 transition"
                          >
                            Confirm
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
