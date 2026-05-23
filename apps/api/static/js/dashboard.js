async function loadMachines() {
  const target = document.getElementById("machine-list");
  const online = document.getElementById("online-count");
  const offline = document.getElementById("offline-count");
  try {
    const res = await fetch("/api/machines");
    const machines = res.ok ? await res.json() : [];
    if (online) online.textContent = machines.filter(m => m.status === "online").length;
    if (offline) offline.textContent = machines.filter(m => m.status !== "online").length;
    const active = document.getElementById("active-count");
    const recent = document.getElementById("recent-count");
    if (active) active.textContent = "0";
    if (recent) recent.textContent = machines.length ? "1" : "0";
    target.innerHTML = machines.length ? machines.map(m => `
      <div class="table-row">
        <strong>${m.hostname}</strong>
        <span class="status-${m.status}">${m.status}</span>
        <span>${m.os}</span>
        <a href="/admin/machines/${m.machine_id}">Open</a>
      </div>`).join("") : `<div class="table-row"><strong>Fake demo machine not enrolled yet</strong><span>offline</span><span>Run fake agent</span><span></span></div>`;
  } catch (err) {
    target.innerHTML = `<div class="table-row"><strong>Unable to load machines</strong><span>${err}</span><span></span><span></span></div>`;
  }
}
document.getElementById("refresh")?.addEventListener("click", loadMachines);
loadMachines();

