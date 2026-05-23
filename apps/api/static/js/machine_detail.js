const machineId = window.MACHINE_ID;
let ws = null;
let controlled = false;

function setStatus(button, state) {
  button.classList.remove("loading");
  if (state === "loading") button.classList.add("loading");
}

async function loadMachine() {
  const res = await fetch(`/api/machines/${machineId}`);
  if (!res.ok) return;
  const machine = await res.json();
  document.getElementById("machine-title").textContent = machine.hostname;
  document.getElementById("machine-meta").textContent = `${machine.status} - ${machine.os} - ${machine.username}`;
}

async function loadAudit() {
  const params = new URLSearchParams();
  const eventType = document.getElementById("audit-event-filter")?.value;
  const actorType = document.getElementById("audit-actor-filter")?.value;
  const start = document.getElementById("audit-start-filter")?.value;
  const end = document.getElementById("audit-end-filter")?.value;
  if (eventType) params.set("event_type", eventType);
  if (actorType) params.set("actor_type", actorType);
  if (start) params.set("start", new Date(start).toISOString());
  if (end) params.set("end", new Date(end).toISOString());
  const res = await fetch(`/api/machines/${machineId}/audit?${params.toString()}`);
  if (!res.ok) return;
  const rows = await res.json();
  const html = rows.map(row => `<div class="audit-item"><strong>${row.event_type}</strong> <span class="muted">${row.actor_type}</span><br>${row.summary}<br><small>${row.created_at}</small><pre>${JSON.stringify(row.metadata_json, null, 2)}</pre></div>`).join("");
  document.getElementById("audit-list").innerHTML = html || "No audit events yet.";
  document.getElementById("recent-audit").innerHTML = html || "No audit events yet.";
}

async function getWsTicket() {
  const res = await fetch("/api/ws-ticket", {method: "POST"});
  if (!res.ok) throw new Error("Unable to issue WebSocket ticket");
  return (await res.json()).ws_ticket;
}

async function connectRelay() {
  if (ws) return;
  const wsTicket = await getWsTicket();
  ws = new WebSocket("ws://localhost:8001/ws/admin");
  ws.addEventListener("open", () => ws.send(JSON.stringify({type:"auth", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:null, session_id:null, payload:{ws_ticket:wsTicket}})));
  ws.addEventListener("message", event => {
    const msg = JSON.parse(event.data);
    if (msg.type === "frame" && msg.payload.jpeg_b64) {
      document.getElementById("remote-screen").src = `data:image/jpeg;base64,${msg.payload.jpeg_b64}`;
    }
    if (msg.type === "command_result") {
      const text = JSON.stringify(msg.payload, null, 2);
      document.getElementById("process-output").textContent = text;
      document.getElementById("apps-output").textContent = text;
    }
  });
}

async function loadFilesAndJobs() {
  const filesRes = await fetch(`/api/files/machines/${machineId}`);
  if (filesRes.ok) {
    const files = await filesRes.json();
    document.getElementById("files-output").innerHTML = files.map(file => `<div class="table-row"><strong>${file.filename}</strong><span>${file.size} bytes</span><span>${file.sha256.slice(0, 12)}</span><span>${file.job_id}</span></div>`).join("") || "No sandbox files.";
  }
  const jobsRes = await fetch(`/api/jobs/machines/${machineId}/history`);
  if (jobsRes.ok) {
    const jobs = await jobsRes.json();
    document.getElementById("jobs-output").innerHTML = jobs.map(job => `<div class="table-row"><strong>${job.command}</strong><span>${job.status}</span><span>${job.exit_code ?? "-"}</span><span>${job.duration_seconds ?? "-"}</span><pre>${job.stdout_preview || job.stderr_preview || ""}</pre></div>`).join("") || "No jobs yet.";
  }
}

document.querySelectorAll(".tabs button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tabs button,.tab-panel").forEach(el => el.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(`tab-${button.dataset.tab}`).classList.add("active");
  });
});

document.getElementById("claim-control").addEventListener("click", event => {
  connectRelay().catch(err => alert(err.message));
  setTimeout(() => {
    ws.send(JSON.stringify({type:"subscribe_machine", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:machineId, session_id:null, payload:{control:true}}));
    controlled = true;
  }, 200);
});

document.getElementById("release-control").addEventListener("click", () => { controlled = false; ws?.close(); ws = null; });
document.querySelectorAll("[data-command]").forEach(button => button.addEventListener("click", () => {
  connectRelay().catch(err => alert(err.message));
  setTimeout(() => ws.send(JSON.stringify({type:"command", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:machineId, session_id:null, payload:{action:button.dataset.command}})), 200);
}));
document.querySelectorAll("[data-danger]").forEach(button => button.addEventListener("click", () => {
  if (document.getElementById("danger-confirm").value !== "CONFIRM") return alert("Type CONFIRM first.");
  alert(`${button.dataset.danger} request recorded for demo audit.`);
}));
document.getElementById("start-screen").addEventListener("click", () => connectRelay().catch(err => alert(err.message)));
document.getElementById("stop-screen").addEventListener("click", () => { ws?.close(); ws = null; });
document.getElementById("refresh-audit")?.addEventListener("click", loadAudit);
document.getElementById("refresh-files")?.addEventListener("click", loadFilesAndJobs);
loadMachine();
loadAudit();
loadFilesAndJobs();
