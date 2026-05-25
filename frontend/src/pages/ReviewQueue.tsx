import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, EmissionActivity } from "../api";

const FLAG_LABELS: Record<string, string> = {
  unit_mismatch: "Unit mismatch",
  missing_distance: "Distance inferred",
  billing_period_gap: "Non-calendar billing period",
  unknown_plant: "Unknown plant code",
  high_quantity: "High quantity",
  duplicate_suspected: "Possible duplicate",
};

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function ReviewQueue({ orgId }: { orgId: number }) {
  const [params] = useSearchParams();
  const [activities, setActivities] = useState<EmissionActivity[]>([]);
  const [selected, setSelected] = useState<EmissionActivity | null>(null);
  const [statusFilter, setStatusFilter] = useState(params.get("status") || "");
  const [scopeFilter, setScopeFilter] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    const q: Record<string, string> = {};
    if (statusFilter) q.status = statusFilter;
    if (scopeFilter) q.scope = scopeFilter;
    if (params.get("flagged") === "true") q.flagged = "true";
    api.activities(orgId, q).then((data) => {
      const list = data.results || [];
      setActivities(list);
      if (list.length && !selected) setSelected(list[0]);
    });
  }, [orgId, statusFilter, scopeFilter, params, selected]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(action: "approve" | "reject" | "lock") {
    if (!selected) return;
    setLoading(true);
    try {
      if (action === "approve") await api.approve(orgId, selected.id, note);
      else if (action === "reject") await api.reject(orgId, selected.id, note);
      else await api.lock(orgId, selected.id);
      setNote("");
      load();
      const updated = await api.activities(orgId, { status: statusFilter });
      const found = (updated.results || []).find((a) => a.id === selected.id);
      setSelected(found || null);
    } finally {
      setLoading(false);
    }
  }

  async function bulkApprove() {
    if (!selectedIds.size) return;
    setLoading(true);
    await api.bulkApprove(orgId, [...selectedIds]);
    setSelectedIds(new Set());
    load();
    setLoading(false);
  }

  function toggleSelect(id: number) {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>Review Queue</h1>
      <p style={{ color: "var(--muted)", marginBottom: "1.5rem" }}>
        Inspect normalized rows, resolve flags, approve or reject before audit lock.
      </p>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="flagged">Flagged</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="locked">Locked</option>
        </select>
        <select value={scopeFilter} onChange={(e) => setScopeFilter(e.target.value)}>
          <option value="">All scopes</option>
          <option value="1">Scope 1</option>
          <option value="2">Scope 2</option>
          <option value="3">Scope 3</option>
        </select>
        <button
          className="btn-success"
          onClick={bulkApprove}
          disabled={!selectedIds.size || loading}
        >
          Bulk approve ({selectedIds.size})
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "1.5rem" }}>
        <div style={{ background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)" }}>
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Date</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Qty</th>
                <th>Status</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => setSelected(a)}
                  style={{
                    cursor: "pointer",
                    background: selected?.id === a.id ? "var(--surface-hover)" : undefined,
                  }}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(a.id)}
                      onChange={() => toggleSelect(a.id)}
                      disabled={a.review_status === "locked" || a.review_status === "approved"}
                    />
                  </td>
                  <td>{a.activity_date}</td>
                  <td className={`scope-${a.scope}`}>S{a.scope}</td>
                  <td>{a.category.replace(/_/g, " ")}</td>
                  <td className="mono">
                    {a.quantity_normalized} {a.unit_normalized}
                  </td>
                  <td>
                    <StatusBadge status={a.review_status} />
                  </td>
                  <td>
                    {a.suspicion_flags?.map((f) => (
                      <span key={f} className="flag-chip">
                        {FLAG_LABELS[f] || f}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selected && (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "1.25rem",
              position: "sticky",
              top: "1rem",
              maxHeight: "calc(100vh - 4rem)",
              overflow: "auto",
            }}
          >
            <h3 style={{ marginBottom: "1rem", fontSize: "1rem" }}>Row #{selected.id}</h3>

            <dl style={{ fontSize: "0.8rem", marginBottom: "1rem" }}>
              <dt style={{ color: "var(--muted)" }}>Description</dt>
              <dd style={{ marginBottom: 8 }}>{selected.description || "—"}</dd>
              <dt style={{ color: "var(--muted)" }}>Source</dt>
              <dd style={{ marginBottom: 8 }}>{selected.data_source_type}</dd>
              <dt style={{ color: "var(--muted)" }}>Site / plant</dt>
              <dd style={{ marginBottom: 8 }}>
                {selected.site_name || "—"} {selected.plant_code && `(${selected.plant_code})`}
              </dd>
              <dt style={{ color: "var(--muted)" }}>Period</dt>
              <dd style={{ marginBottom: 8 }}>
                {selected.period_start} → {selected.period_end}
              </dd>
              <dt style={{ color: "var(--muted)" }}>Raw → normalized</dt>
              <dd className="mono" style={{ marginBottom: 8 }}>
                {selected.quantity_raw} {selected.unit_raw} → {selected.quantity_normalized}{" "}
                {selected.unit_normalized}
              </dd>
              <dt style={{ color: "var(--muted)" }}>Reference</dt>
              <dd className="mono">{selected.source_reference || "—"}</dd>
            </dl>

            {selected.suspicion_flags?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--warn)", marginBottom: 4 }}>Suspicion flags</div>
                {selected.suspicion_flags.map((f) => (
                  <span key={f} className="flag-chip">
                    {FLAG_LABELS[f] || f}
                  </span>
                ))}
              </div>
            )}

            <textarea
              placeholder="Analyst note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              style={{ width: "100%", marginBottom: "1rem" }}
            />

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {selected.review_status !== "locked" && selected.review_status !== "approved" && (
                <>
                  <button className="btn-success" onClick={() => act("approve")} disabled={loading}>
                    Approve
                  </button>
                  <button className="btn-danger" onClick={() => act("reject")} disabled={loading}>
                    Reject
                  </button>
                </>
              )}
              {selected.review_status === "approved" && (
                <button className="btn-primary" onClick={() => act("lock")} disabled={loading}>
                  Lock for audit
                </button>
              )}
            </div>

            {selected.audit_logs?.length > 0 && (
              <div style={{ marginTop: "1.5rem", borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 8 }}>Audit trail</div>
                {selected.audit_logs.map((log, i) => (
                  <div key={i} style={{ fontSize: "0.7rem", marginBottom: 6, color: "var(--muted)" }}>
                    <span className="mono">{log.created_at?.slice(0, 16)}</span> — {log.action} by{" "}
                    {log.user_name || "system"}
                    {log.note && `: ${log.note}`}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
