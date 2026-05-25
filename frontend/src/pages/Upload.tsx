import { useEffect, useState } from "react";
import { api, DataSource, IngestionBatch } from "../api";

const SOURCE_HELP: Record<string, string> = {
  sap_mm:
    "SAP MM flat-file export (semicolon-delimited). Fuel & procurement with DE/EN column aliases.",
  utility_portal:
    "Utility portal CSV with billing periods, meter IDs, and kWh consumption.",
  travel_concur:
    "Concur-style expense report CSV. Flights, hotels, ground — distances may be missing.",
};

export default function Upload({ orgId }: { orgId: number }) {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<IngestionBatch | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.sources(orgId).then((list) => {
      setSources(list);
      if (list.length) setSelected(list[0].id);
    });
  }, [orgId]);

  async function handleUpload() {
    if (!file || !selected) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const batch = await api.upload(orgId, selected, file);
      setResult(batch);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  const current = sources.find((s) => s.id === selected);

  return (
    <div>
      <h1 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>Ingest Data</h1>
      <p style={{ color: "var(--muted)", marginBottom: "2rem" }}>
        Upload source files. Each source type has its own parser and normalization rules.
      </p>

      <div
        style={{
          maxWidth: 560,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "1.5rem",
        }}
      >
        <label style={{ fontSize: "0.75rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>
          Data source
        </label>
        <select
          value={selected ?? ""}
          onChange={(e) => setSelected(Number(e.target.value))}
          style={{ width: "100%", marginBottom: "1rem" }}
        >
          {sources.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>

        {current && (
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "1.25rem" }}>
            {SOURCE_HELP[current.source_type] || current.source_type}
          </p>
        )}

        <input
          type="file"
          accept=".csv,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          style={{ width: "100%", marginBottom: "1.25rem" }}
        />

        <button className="btn-primary" onClick={handleUpload} disabled={!file || loading}>
          {loading ? "Processing…" : "Upload & normalize"}
        </button>

        {error && <p style={{ color: "var(--danger)", marginTop: "1rem", fontSize: "0.875rem" }}>{error}</p>}

        {result && (
          <div
            style={{
              marginTop: "1.5rem",
              padding: "1rem",
              background: "var(--bg)",
              borderRadius: 6,
              border: "1px solid var(--border)",
            }}
          >
            <strong>Ingestion complete</strong>
            <ul style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "var(--muted)", listStyle: "none" }}>
              <li>Rows parsed: {result.row_count}</li>
              <li style={{ color: "var(--success)" }}>Normalized: {result.success_count}</li>
              <li style={{ color: result.error_count ? "var(--danger)" : "var(--muted)" }}>
                Errors: {result.error_count}
              </li>
              <li style={{ color: result.warning_count ? "var(--warn)" : "var(--muted)" }}>
                Warnings (flagged): {result.warning_count}
              </li>
            </ul>
            <a href="/review" style={{ color: "var(--accent)", fontSize: "0.875rem" }}>
              → Go to review queue
            </a>
          </div>
        )}
      </div>

      <div style={{ marginTop: "2rem", fontSize: "0.8rem", color: "var(--muted)" }}>
        <strong>Sample files to upload</strong> — folder:{" "}
        <span className="mono">sample_data\</span>
        <table style={{ marginTop: "0.75rem", fontSize: "0.8rem" }}>
          <thead>
            <tr>
              <th>Data source</th>
              <th>File</th>
              <th>Format</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>SAP MM — Fuel & Procurement</td>
              <td className="mono">sap_mm_export.csv</td>
              <td>CSV, semicolon (;)</td>
            </tr>
            <tr>
              <td>Utility Portal — Electricity</td>
              <td className="mono">utility_portal_export.csv</td>
              <td>CSV, comma (,)</td>
            </tr>
            <tr>
              <td>Concur — Business Travel</td>
              <td className="mono">concur_travel_export.csv</td>
              <td>CSV, comma (,)</td>
            </tr>
          </tbody>
        </table>
        <p style={{ marginTop: "0.5rem" }}>
          See <span className="mono">sample_data/README.md</span> for column definitions.
        </p>
      </div>
    </div>
  );
}
