import { Link, useLocation } from "react-router-dom";
import { Organization, User } from "../api";

interface Props {
  user: User;
  orgs: Organization[];
  orgId: number;
  onOrgChange: (id: number) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

export default function Layout({ user, orgs, orgId, onOrgChange, onLogout, children }: Props) {
  const loc = useLocation();
  const nav = [
    { path: "/", label: "Dashboard" },
    { path: "/upload", label: "Ingest Data" },
    { path: "/review", label: "Review Queue" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 240,
          background: "var(--surface)",
          borderRight: "1px solid var(--border)",
          padding: "1.5rem 1rem",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontWeight: 700, fontSize: "1.1rem", letterSpacing: "-0.02em" }}>
            Breathe ESG
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 4 }}>
            Analyst Review Portal
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          {nav.map((n) => (
            <Link
              key={n.path}
              to={n.path}
              style={{
                display: "block",
                padding: "0.6rem 0.75rem",
                marginBottom: 4,
                borderRadius: 6,
                textDecoration: "none",
                color: loc.pathname === n.path ? "#fff" : "var(--muted)",
                background: loc.pathname === n.path ? "var(--accent)" : "transparent",
                fontWeight: loc.pathname === n.path ? 600 : 400,
              }}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
          <label style={{ fontSize: "0.7rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>
            Organization
          </label>
          <select
            value={orgId}
            onChange={(e) => onOrgChange(Number(e.target.value))}
            style={{ width: "100%", marginBottom: "0.75rem" }}
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
          <div style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}>{user.username}</div>
          <button className="btn-secondary" style={{ width: "100%" }} onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: "2rem", overflow: "auto" }}>{children}</main>
    </div>
  );
}
