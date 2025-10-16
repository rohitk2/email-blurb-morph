import React, { useEffect, useState } from "react";

type LogDoc = {
  request_id: string;
  source_hash: string;
  cache_hit: boolean;
  latency: number;
  timestamp: any;
};

function parseTimestamp(ts: any): Date | null {
  try {
    if (typeof ts === "string") return new Date(ts);
    if (ts?.$date) return new Date(ts.$date);
    if (ts?.$date?.$numberLong) return new Date(Number(ts.$date.$numberLong));
  } catch {}
  return null;
}

export default function Logging() {
  const [rows, setRows] = useState<LogDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url =
      import.meta.env.VITE_API_BASE_URL
        ? `${import.meta.env.VITE_API_BASE_URL}/logging`
        : "http://localhost:8000/logging";

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setRows(json || []);
      })
      .catch((err: any) => setError(err?.message ?? String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h1>View Logging</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {!loading && !error && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Request ID</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Source Hash</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Cache Hit</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Latency (ms)</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => {
              const d = parseTimestamp(r.timestamp);
              return (
                <tr key={r.request_id ?? `row-${idx}`}>
                  <td style={{ padding: "8px 0" }}>{r.request_id}</td>
                  <td style={{ padding: "8px 0" }}>{r.source_hash}</td>
                  <td style={{ padding: "8px 0" }}>{String(r.cache_hit)}</td>
                  <td style={{ padding: "8px 0" }}>{r.latency}</td>
                  <td style={{ padding: "8px 0" }}>{d ? d.toLocaleString() : String(r.timestamp)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}