import React, { useEffect, useState } from "react";

type MetricDoc = {
  _id?: string | { $oid: string };
  tokens_used: number;
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

export default function Metrics() {
  const [rows, setRows] = useState<MetricDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const url =
      import.meta.env.VITE_API_BASE_URL
        ? `${import.meta.env.VITE_API_BASE_URL}/metrics`
        : "http://localhost:8000/metrics";

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
      <h1>Metrics</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {!loading && !error && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Tokens Used</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Latency (ms)</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => {
              const d = parseTimestamp(r.timestamp);
              return (
                <tr key={idx}>
                  <td style={{ padding: "8px 0" }}>{r.tokens_used}</td>
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