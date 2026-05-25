import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { api, Organization, User } from "./api";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import ReviewQueue from "./pages/ReviewQueue";
import Upload from "./pages/Upload";
import Layout from "./components/Layout";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgId, setOrgId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((data) => {
        setUser(data.user);
        setOrgs(data.organizations);
        if (data.organizations.length) {
          const saved = localStorage.getItem("orgId");
          setOrgId(saved ? Number(saved) : data.organizations[0].id);
        }
      })
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  const onLogin = (token: string, u: User, organizations: Organization[]) => {
    localStorage.setItem("token", token);
    setUser(u);
    setOrgs(organizations);
    if (organizations.length) {
      setOrgId(organizations[0].id);
      localStorage.setItem("orgId", String(organizations[0].id));
    }
  };

  const onLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("orgId");
    setUser(null);
    setOrgs([]);
    setOrgId(null);
  };

  if (loading) {
    return <div style={{ padding: "2rem", color: "var(--muted)" }}>Loading…</div>;
  }

  if (!user) {
    return <Login onLogin={onLogin} />;
  }

  if (!orgId) {
    return <div style={{ padding: "2rem" }}>No organization assigned.</div>;
  }

  return (
    <BrowserRouter>
      <Layout
        user={user}
        orgs={orgs}
        orgId={orgId}
        onOrgChange={(id) => {
          setOrgId(id);
          localStorage.setItem("orgId", String(id));
        }}
        onLogout={onLogout}
      >
        <Routes>
          <Route path="/" element={<Dashboard orgId={orgId} />} />
          <Route path="/upload" element={<Upload orgId={orgId} />} />
          <Route path="/review" element={<ReviewQueue orgId={orgId} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
