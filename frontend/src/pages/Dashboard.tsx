import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DashboardStats } from "../api";

export default function Dashboard({ orgId }: { orgId: number }) {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.dashboard(orgId).then(setStats);
  }, [orgId]);

  if (!stats) return <p style={{ color: "var(--muted)" }}>Loading dashboard…</p>;

  const cards = [
    { label: "Total activities", value: stats.total_activities, color: "var(--text)" },
    { label: "Pending review", value: stats.pending_review, color: "var(--muted)" },
    { label: "Flagged / suspicious", value: stats.flagged, color: "var(--warn)" },
    { label: "Approved", value: stats.approved, color: "var(--success)" },
    { label: "Locked for audit", value: stats.locked, color: "var(--scope1)" },
    { label: "Failed ingestions", value: stats.failed_batches, color: "var(--danger)" },
  ];

  return (
    <div>
      <h1 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>Review Dashboard</h1>
      <p style={{ color: "var(--muted)", marginBottom: "2rem" }}>
        What came in, what failed, what needs attention before audit lock.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
          gap: "1rem",
          marginBottom: "2.5rem",
        }}
      >
        {cards.map((c) => (
          <div
            key={c.label}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "1.25rem",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: 8 }}>{c.label}</div>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem" }}>
        <Link to="/upload" className="btn-primary" style={{ textDecoration: "none", display: "inline-block" }}>
          Upload new data
        </Link>
        <Link
          to="/review?status=flagged"
          className="btn-secondary"
          style={{ textDecoration: "none", display: "inline-block" }}
        >
          Review flagged rows
        </Link>
        <Link
          to="/review?status=pending"
          className="btn-secondary"
          style={{ textDecoration: "none", display: "inline-block" }}
        >
          Review pending
        </Link>
      </div>

      <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Recent ingestions</h2>
      <div style={{ background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)" }}>
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Source</th>
              <th>Status</th>
              <th>Rows</th>
              <th>OK</th>
              <th>Errors</th>
              <th>Warnings</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_batches.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)", textAlign: "center" }}>
                  No ingestions yet — upload sample files from /sample_data
                </td>
              </tr>
            ) : (
              stats.recent_batches.map((b) => (
                <tr key={b.id}>
                  <td className="mono">{b.filename}</td>
                  <td>{b.data_source_label}</td>
                  <td>
                    <span className={`badge badge-${b.status === "completed" ? "approved" : "pending"}`}>
                      {b.status}
                    </span>
                  </td>
                  <td>{b.row_count}</td>
                  <td style={{ color: "var(--success)" }}>{b.success_count}</td>
                  <td style={{ color: b.error_count ? "var(--danger)" : "var(--muted)" }}>{b.error_count}</td>
                  <td style={{ color: b.warning_count ? "var(--warn)" : "var(--muted)" }}>{b.warning_count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
