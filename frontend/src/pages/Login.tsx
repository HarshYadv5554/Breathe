import { FormEvent, useState } from "react";
import { api, Organization, User } from "../api";

interface Props {
  onLogin: (token: string, user: User, orgs: Organization[]) => void;
}

export default function Login({ onLogin }: Props) {
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("breathe2026");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.login(username, password);
      onLogin(data.token, data.user, data.organizations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(145deg, #0f1419 0%, #1a2a32 50%, #0f1419 100%)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: 380,
          background: "var(--surface)",
          padding: "2.5rem",
          borderRadius: 12,
          border: "1px solid var(--border)",
        }}
      >
        <h1 style={{ fontSize: "1.5rem", marginBottom: "0.25rem" }}>Breathe ESG</h1>
        <p style={{ color: "var(--muted)", fontSize: "0.875rem", marginBottom: "2rem" }}>
          Emissions data review — analyst sign-in
        </p>

        <label style={{ display: "block", fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4 }}>
          Username
        </label>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ width: "100%", marginBottom: "1rem" }}
          autoComplete="username"
        />

        <label style={{ display: "block", fontSize: "0.75rem", color: "var(--muted)", marginBottom: 4 }}>
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", marginBottom: "1.5rem" }}
          autoComplete="current-password"
        />

        {error && (
          <p style={{ color: "var(--danger)", fontSize: "0.8rem", marginBottom: "1rem" }}>{error}</p>
        )}

        <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>

        <p style={{ marginTop: "1.5rem", fontSize: "0.75rem", color: "var(--muted)" }}>
          Demo: analyst / breathe2026
        </p>
      </form>
    </div>
  );
}
