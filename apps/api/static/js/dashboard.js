const state = { machines: [] };

const fmtDate = value => value ? new Date(value).toLocaleString() : "never";
const statusPill = status => `<span class="status-pill status-${status}"><span class="status-dot"></span>${status}</span>`;
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} failed: ${res.status}`);
  return res.json();
}

function renderMachines() {
  const target = document.getElementById("machine-list");
  const query = document.getElementById("dashboard-search")?.value?.toLowerCase() || "";
  const rows = state.machines.filter(m => [m.hostname, m.os, m.machine_id].join(" ").toLowerCase().includes(query)).slice(0, 8);
  target.innerHTML = rows.map(m => `
    <tr>
      <td><strong>${escapeHtml(m.hostname)}</strong><br><small class="muted">${escapeHtml(m.username)}</small></td>
      <td>${escapeHtml(m.machine_id)}</td>
      <td>${escapeHtml(m.os)}</td>
      <td>${statusPill(m.status)}</td>
      <td><a class="btn" href="/admin/machines/${encodeURIComponent(m.machine_id)}">Manage</a></td>
    </tr>`).join("") || `<tr><td class="empty-row" colspan="5">No machines yet. Run <code>python scripts/run_3_fake_agents.py</code>.</td></tr>`;
}

function renderAudit(rows) {
  document.getElementById("recent-audit").innerHTML = rows.map(row => `
    <div class="audit-item">
      <strong>${escapeHtml(row.event_type)}</strong>
      <small>${escapeHtml(row.machine_id || "global")} · ${escapeHtml(row.actor_type)} · ${fmtDate(row.created_at)}</small>
      <span>${escapeHtml(row.summary)}</span>
    </div>`).join("") || `<div class="audit-item"><span>No audit events yet.</span></div>`;
}

async function loadDashboard() {
  const [summary, machines, audit] = await Promise.all([
    getJson("/api/dashboard/summary"),
    getJson("/api/machines"),
    getJson("/api/dashboard/recent-audit?limit=8"),
  ]);
  state.machines = machines;
  document.getElementById("online-count").textContent = summary.online_machines;
  document.getElementById("stale-count").textContent = summary.stale_machines + summary.offline_machines;
  document.getElementById("active-count").textContent = summary.active_sessions;
  document.getElementById("commands-count").textContent = summary.commands_today;
  document.getElementById("alerts-count").textContent = `${summary.alerts} alerts`;
  renderMachines();
  renderAudit(audit);
}

document.getElementById("refresh")?.addEventListener("click", () => loadDashboard().catch(alert));
document.getElementById("dashboard-search")?.addEventListener("input", renderMachines);
loadDashboard().catch(err => {
  document.getElementById("machine-list").innerHTML = `<tr><td class="empty-row" colspan="5">${escapeHtml(err.message)}</td></tr>`;
});
