const BASE = "/api";

// Demo role; in production this comes from the auth/JWT layer.
const headers = { "X-Role": "admin", "X-User": "demo@nexuszenith" };

export async function getHealth() {
  const r = await fetch(`${BASE}/health`);
  return r.json();
}
export async function getDashboard() {
  const r = await fetch(`${BASE}/dashboard`, { headers });
  return r.json();
}
export async function getDashboardMetrics() {
  const r = await fetch(`${BASE}/dashboard/metrics`, { headers });
  return r.json();
}

export async function getDashboardNarrative() {
  const r = await fetch(`${BASE}/dashboard/narrative`, { headers });
  return r.json();
}

export async function getDashboardCapabilities() {
  const r = await fetch(`${BASE}/dashboard/capabilities`, { headers });
  return r.json();
}

export async function getCopilotSuggestions() {
  const r = await fetch(`${BASE}/copilot/suggestions`, { headers });
  return r.json();
}

export async function getCopilotExamples() {
  const r = await fetch(`${BASE}/copilot/examples`, { headers });
  return r.json();
}

export async function askCopilot(prompt) {
  const r = await fetch(`${BASE}/copilot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(`Copilot query failed (${r.status})`);
  return r.json();
}
export async function getScans() {
  const r = await fetch(`${BASE}/scans`, { headers });
  return r.json();
}
export async function getAudit() {
  const r = await fetch(`${BASE}/audit`, { headers });
  return r.json();
}
export async function scanFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/scan`, { method: "POST", headers, body: fd });
  if (!r.ok) throw new Error(`Scan failed (${r.status})`);
  return r.json();
}

export const SEV = {
  P1: { label: "Critical", color: "var(--p1)" },
  P2: { label: "High", color: "var(--p2)" },
  P3: { label: "Medium", color: "var(--p3)" },
  P4: { label: "Low", color: "var(--p4)" },
};

export const REG_LABEL = {
  gdpr: "GDPR",
  iso27001: "ISO 27001",
  sox: "SOX",
  internal_security: "Internal Security",
  internal_hr: "Internal HR",
};
