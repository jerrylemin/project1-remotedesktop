const machineId = window.MACHINE_ID;
let token = localStorage.getItem("telepc_token") || "";
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
  document.getElementById("machine-meta").textContent = `${machine.status} · ${machine.os} · ${machine.username}`;
}

async function loadAudit() {
  const res = await fetch(`/api/machines/${machineId}/audit`);
  if (!res.ok) return;
  const rows = await res.json();
  const html = rows.map(row => `<div><strong>${row.event_type}</strong> ${row.summary}<br><small>${row.created_at}</small></div>`).join("");
  document.getElementById("audit-list").innerHTML = html || "No audit events yet.";
  document.getElementById("recent-audit").innerHTML = html || "No audit events yet.";
}

function connectRelay() {
  if (ws) return;
  ws = new WebSocket("ws://localhost:8001/ws/admin");
  ws.addEventListener("open", () => ws.send(JSON.stringify({type:"auth", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:null, session_id:null, payload:{token}})));
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

document.querySelectorAll(".tabs button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tabs button,.tab-panel").forEach(el => el.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(`tab-${button.dataset.tab}`).classList.add("active");
  });
});

document.getElementById("claim-control").addEventListener("click", event => {
  connectRelay();
  setTimeout(() => {
    ws.send(JSON.stringify({type:"subscribe_machine", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:machineId, session_id:null, payload:{control:true}}));
    controlled = true;
  }, 200);
});

document.getElementById("release-control").addEventListener("click", () => { controlled = false; ws?.close(); ws = null; });
document.querySelectorAll("[data-command]").forEach(button => button.addEventListener("click", () => {
  connectRelay();
  setTimeout(() => ws.send(JSON.stringify({type:"command", msg_id:crypto.randomUUID(), ts:new Date().toISOString(), machine_id:machineId, session_id:null, payload:{action:button.dataset.command}})), 200);
}));
document.querySelectorAll("[data-danger]").forEach(button => button.addEventListener("click", () => {
  if (document.getElementById("danger-confirm").value !== "CONFIRM") return alert("Type CONFIRM first.");
  alert(`${button.dataset.danger} request recorded for demo audit.`);
}));
document.getElementById("start-screen").addEventListener("click", connectRelay);
document.getElementById("stop-screen").addEventListener("click", () => { ws?.close(); ws = null; });
loadMachine();
loadAudit();
