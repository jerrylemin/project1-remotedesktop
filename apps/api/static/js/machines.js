const machineState = { rows: [] };
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const fmtDate = value => value ? new Date(value).toLocaleString() : "never";
const statusPill = status => `<span class="status-pill status-${status}"><span class="status-dot"></span>${status}</span>`;

async function loadMachines() {
  const res = await fetch("/api/machines");
  if (!res.ok) throw new Error("Unable to load machines");
  machineState.rows = await res.json();
  renderMachines();
}

function renderMachines() {
  const query = (document.getElementById("machine-search")?.value || "").toLowerCase();
  const filter = document.getElementById("status-filter")?.value || "";
  const rows = machineState.rows.filter(m => {
    const matchesText = [m.hostname, m.os, m.username, m.machine_id].join(" ").toLowerCase().includes(query);
    const matchesStatus = !filter || m.status === filter;
    return matchesText && matchesStatus;
  });
  document.getElementById("machine-list").innerHTML = rows.map(m => `
    <tr>
      <td><strong>${escapeHtml(m.hostname)}</strong><br><small class="muted">${escapeHtml(m.username)}</small></td>
      <td>${escapeHtml(m.machine_id)}</td>
      <td>${escapeHtml(m.os)}</td>
      <td>${statusPill(m.status)}</td>
      <td>${fmtDate(m.last_seen)}</td>
      <td>${m.active_controller_user_id ? `user #${m.active_controller_user_id}` : "none"}</td>
      <td><a class="btn" href="/admin/machines/${encodeURIComponent(m.machine_id)}">Manage</a></td>
    </tr>`).join("") || `<tr><td class="empty-row" colspan="7">No machines match the current filter.</td></tr>`;
}

document.getElementById("refresh")?.addEventListener("click", () => loadMachines().catch(alert));
document.getElementById("machine-search")?.addEventListener("input", renderMachines);
document.getElementById("status-filter")?.addEventListener("change", renderMachines);
loadMachines().catch(alert);
