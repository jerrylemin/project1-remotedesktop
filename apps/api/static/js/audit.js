const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const statusPill = status => `<span class="status-pill status-${status}"><span class="status-dot"></span>${status}</span>`;

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} failed`);
  return res.json();
}

async function loadAuditIndex() {
  const [machines, audit] = await Promise.all([getJson("/api/machines"), getJson("/api/dashboard/recent-audit?limit=12")]);
  document.getElementById("machine-list").innerHTML = machines.map(m => `
    <tr>
      <td><strong>${escapeHtml(m.hostname)}</strong><br><small class="muted">${escapeHtml(m.machine_id)}</small></td>
      <td>${statusPill(m.status)}</td>
      <td><a class="btn secondary" href="/admin/machines/${encodeURIComponent(m.machine_id)}">Open Logs</a></td>
    </tr>`).join("") || `<tr><td class="empty-row" colspan="3">No machines found.</td></tr>`;
  document.getElementById("recent-audit").innerHTML = audit.map(row => `
    <div class="audit-item"><strong>${escapeHtml(row.event_type)}</strong><small>${escapeHtml(row.machine_id || "global")} · ${new Date(row.created_at).toLocaleString()}</small><span>${escapeHtml(row.summary)}</span></div>
  `).join("") || `<div class="audit-item">No audit events yet.</div>`;
}

document.getElementById("refresh")?.addEventListener("click", () => loadAuditIndex().catch(alert));
loadAuditIndex().catch(alert);
