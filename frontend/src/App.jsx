import { useEffect, useState } from "react";

const API = "http://localhost:8000";

export default function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    fetch(`${API}/api/health`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("backend not reachable"));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: 24 }}>
      <h1>AI Dataset Advisor</h1>
      <p>Backend status: <strong>{status}</strong></p>
    </div>
  );
}
