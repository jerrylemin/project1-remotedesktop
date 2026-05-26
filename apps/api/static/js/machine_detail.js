const machineId = window.MACHINE_ID;
const protectedProcesses = new Set(["lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"]);
let currentSessionId = null;
let lastFrameAt = 0;
let keyboardRunning = false;

const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const fmtDate = value => value ? new Date(value).toLocaleString() : "never";

const wsClient = new TelepcWsClient(machineId, {
  onFrame: jpeg => {
    const src = `data:image/jpeg;base64,${jpeg}`;
    document.getElementById("remote-screen").src = src;
    document.getElementById("download-screen").href = src;
    const now = performance.now();
    if (lastFrameAt) document.getElementById("fps-label").textContent = `${Math.round(1000 / Math.max(1, now - lastFrameAt))} fps`;
    lastFrameAt = now;
  },
  onResult: msg => handleWsResult(msg),
  onStatus: status => {
    const el = document.getElementById("connection-status");
    el.textContent = status;
    el.className = `remote-status ${status}`;
  },
});

async function jsonFetch(url, options = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `${url} failed`);
  return res.json();
}

async function apiCommand(url, options = {}) {
  const response = await jsonFetch(url, options);
  if (response.command) {
    await wsClient.connect({ control: true });
    wsClient.sendCommand(response.command);
  }
  await loadAudit();
  return response;
}

async function loadMachine() {
  const machine = await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}`);
  document.getElementById("machine-title").textContent = machine.hostname;
  document.getElementById("machine-hostname").textContent = machine.hostname;
  document.getElementById("machine-meta").textContent = `${machine.status} · ${machine.os}`;
  document.getElementById("machine-facts").textContent = `machine_id=${machine.machine_id} · user=${machine.username}`;
  document.getElementById("active-controller").textContent = machine.active_controller_user_id ? `user #${machine.active_controller_user_id}` : "none";
  document.getElementById("overview-status").textContent = machine.status;
  document.getElementById("overview-os").textContent = machine.os;
  document.getElementById("overview-user").textContent = machine.username;
  document.getElementById("overview-last-seen").textContent = fmtDate(machine.last_seen);
}

function switchPanel(panel) {
  document.querySelectorAll(".module-link,.remote-panel").forEach(el => el.classList.remove("active"));
  document.querySelector(`[data-panel="${panel}"]`)?.classList.add("active");
  document.getElementById(`panel-${panel}`)?.classList.add("active");
  if (panel === "apps") loadApplications().catch(alert);
  if (panel === "processes") loadProcesses().catch(alert);
  if (panel === "files") loadFilesAndJobs().catch(alert);
  if (panel === "audit") loadAudit().catch(alert);
}

function handleWsResult(msg) {
  if (msg.type === "error") {
    alert(msg.payload?.detail || "Relay error");
    return;
  }
  const payload = msg.payload || {};
  if (payload.processes) renderProcesses(payload.processes);
  if (payload.applications) renderApplications(payload.applications);
  if (payload.webcam) {
    document.getElementById("webcam-status").textContent = payload.webcam;
    document.getElementById("webcam-preview").textContent = payload.webcam === "started" ? "Webcam active with consent" : "Camera preview starts only after consent.";
  }
  if (payload.action && payload.demo_safe) document.getElementById("power-result").textContent = `${payload.action} accepted for demo-safe agent flow`;
  loadAudit().catch(() => {});
}

function renderApplications(apps) {
  const normalized = apps.map(app => ({ name: app.name || app.command || "unknown", status: app.status || (app.allowed ? "Stopped" : "Blocked"), cpu: app.cpu ?? "0" }));
  document.getElementById("apps-badge").textContent = normalized.length;
  document.getElementById("apps-running").textContent = normalized.filter(app => String(app.status).toLowerCase() === "running").length;
  document.getElementById("apps-high-cpu").textContent = normalized.filter(app => Number(app.cpu) >= 20).length;
  document.getElementById("apps-background").textContent = normalized.filter(app => String(app.status).toLowerCase() !== "running").length;
  document.getElementById("apps-table").innerHTML = normalized.map(app => {
    const running = String(app.status).toLowerCase() === "running";
    return `<tr><td>${esc(app.name)}</td><td><span class="run-badge ${running ? "run" : "idle"}">${esc(app.status)}</span></td><td>${esc(app.cpu)}%</td><td><button class="action-btn ${running ? "kill" : "start"}" data-app="${esc(app.name)}" data-app-action="${running ? "stop" : "start"}">${running ? "Stop" : "Start"}</button></td></tr>`;
  }).join("") || `<tr><td colspan="4">No applications returned.</td></tr>`;
}

function renderProcesses(processes) {
  document.getElementById("process-badge").textContent = processes.length;
  document.getElementById("process-table").innerHTML = processes.map(proc => {
    const name = proc.name || "unknown";
    const protectedName = protectedProcesses.has(String(name).toLowerCase());
    return `<tr><td>${esc(proc.pid)}</td><td>${esc(name)}</td><td>${esc(proc.cpu ?? proc.status ?? "-")}</td><td>${esc(proc.memory ?? proc.ram ?? "-")}</td><td>${protectedName ? "<span class=\"run-badge idle\">Protected</span>" : `<button class="action-btn kill" data-pid="${esc(proc.pid)}" data-process="${esc(name)}">Stop</button>`}</td></tr>`;
  }).join("") || `<tr><td colspan="5">No processes returned.</td></tr>`;
}

async function loadApplications() {
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications`);
}

async function loadProcesses() {
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/processes`);
}

async function loadFilesAndJobs() {
  const [files, jobs] = await Promise.all([
    jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/sandbox/files`),
    jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/sandbox/jobs`),
  ]);
  document.getElementById("files-output").innerHTML = files.map(file => `<div class="stack-item"><strong>${esc(file.filename)}</strong><small>${file.size} bytes · sha256 ${esc(file.sha256).slice(0, 16)} · job ${esc(file.job_id)}</small><small>${esc(file.sandbox_path)} · ${fmtDate(file.uploaded_at)}</small></div>`).join("") || `<div class="stack-item">No sandbox files dispatched.</div>`;
  document.getElementById("jobs-output").innerHTML = jobs.map(job => `<div class="stack-item"><strong>${esc(job.command)}</strong><small>${esc(job.status)} · exit ${job.exit_code ?? "-"} · ${fmtDate(job.started_at)}</small><pre class="metadata-preview">${esc(job.stdout_preview || job.stderr_preview || "")}</pre></div>`).join("") || `<div class="stack-item">No job history.</div>`;
}

async function loadAudit() {
  const filter = document.getElementById("audit-event-filter")?.value || "";
  const suffix = filter ? `?event_type=${encodeURIComponent(filter)}` : "";
  const rows = await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/audit${suffix}`);
  const html = rows.map(row => `<div class="audit-item"><strong>${esc(row.event_type)}</strong><small>${esc(row.actor_type)} · ${fmtDate(row.created_at)} · ${esc(row.machine_id || "")}</small><span>${esc(row.summary)}</span><pre class="metadata-preview">${esc(JSON.stringify(row.metadata_json, null, 2))}</pre></div>`).join("") || `<div class="audit-item">No audit events for this machine.</div>`;
  document.getElementById("audit-list").innerHTML = html;
  document.getElementById("recent-audit").innerHTML = html;
}

function openConfirm(title, message) {
  const modal = document.getElementById("confirm-modal");
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-message").textContent = message;
  document.getElementById("confirm-reason").value = "";
  document.getElementById("confirm-check").checked = false;
  modal.showModal();
  return new Promise(resolve => {
    modal.addEventListener("close", () => resolve({
      ok: modal.returnValue === "confirm",
      reason: document.getElementById("confirm-reason").value,
      confirm: document.getElementById("confirm-check").checked,
    }), { once: true });
  });
}

async function claimControl() {
  const session = await jsonFetch("/api/sessions", { method: "POST", body: JSON.stringify({ machine_id: machineId }) });
  currentSessionId = session.id;
  await wsClient.connect({ control: true });
  await loadMachine();
  await loadAudit();
}

async function releaseControl() {
  if (currentSessionId) await jsonFetch(`/api/sessions/${encodeURIComponent(currentSessionId)}/release`, { method: "POST", body: "{}" });
  currentSessionId = null;
  wsClient.close();
  await loadMachine();
  await loadAudit();
}

document.querySelectorAll(".module-link").forEach(button => button.addEventListener("click", () => switchPanel(button.dataset.panel)));
document.getElementById("claim-control").addEventListener("click", () => claimControl().catch(alert));
document.getElementById("release-control").addEventListener("click", () => releaseControl().catch(alert));
document.getElementById("refresh-processes").addEventListener("click", () => loadProcesses().catch(alert));
document.getElementById("refresh-audit").addEventListener("click", () => loadAudit().catch(alert));
document.getElementById("audit-event-filter").addEventListener("input", () => loadAudit().catch(() => {}));
document.getElementById("refresh-files").addEventListener("click", () => loadFilesAndJobs().catch(alert));

document.getElementById("apps-table").addEventListener("click", async event => {
  const button = event.target.closest("[data-app-action]");
  if (!button) return;
  const action = button.dataset.appAction;
  const name = button.dataset.app;
  if (action === "start") {
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/start`, { method: "POST", body: JSON.stringify({ name, command: name, confirm: true }) });
  } else {
    const decision = await openConfirm("Stop application", `Stop ${name}?`);
    if (decision.ok) await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/stop`, { method: "POST", body: JSON.stringify({ name, confirm: decision.confirm }) });
  }
});

document.getElementById("process-table").addEventListener("click", async event => {
  const button = event.target.closest("[data-pid]");
  if (!button) return;
  const decision = await openConfirm("Stop process", `Stop PID ${button.dataset.pid} (${button.dataset.process})?`);
  if (!decision.ok) return;
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/processes/${encodeURIComponent(button.dataset.pid)}/stop`, { method: "POST", body: JSON.stringify({ name: button.dataset.process, confirm: decision.confirm }) });
});

document.getElementById("start-screen").addEventListener("click", async () => {
  await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/screen/start`, { method: "POST", body: JSON.stringify({ mode: "live", consent: true }) });
  document.getElementById("screen-mode-label").textContent = "Live mode";
  await wsClient.connect({ control: false });
  await loadAudit();
});
document.getElementById("stop-screen").addEventListener("click", async () => {
  await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/screen/stop`, { method: "POST", body: JSON.stringify({ mode: "live", consent: true }) });
  wsClient.close();
  document.getElementById("screen-mode-label").textContent = "Screenshot mode";
  document.getElementById("fps-label").textContent = "0 fps";
  await loadAudit();
});
document.getElementById("capture-screen").addEventListener("click", async () => {
  await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/screen/capture`, { method: "POST", body: JSON.stringify({ mode: "screenshot", consent: true }) });
  await wsClient.connect({ control: false });
  await loadAudit();
});

document.getElementById("upload-file").addEventListener("click", async () => {
  const artifact = await TelepcFiles.uploadArtifact(document.getElementById("file-input"));
  await TelepcFiles.dispatchArtifact(artifact.artifact_id, machineId);
  await loadFilesAndJobs();
  await loadAudit();
});

document.getElementById("webcam-start").addEventListener("click", async () => {
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/start`, { method: "POST", body: JSON.stringify({ consent: document.getElementById("webcam-consent").checked }) });
});
document.getElementById("webcam-stop").addEventListener("click", async () => {
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/stop`, { method: "POST", body: JSON.stringify({ consent: true }) });
});
document.getElementById("webcam-snapshot").addEventListener("click", () => {
  document.getElementById("webcam-preview").textContent = `Snapshot requested at ${new Date().toLocaleTimeString()}`;
});

document.getElementById("keyboard-toggle").addEventListener("click", () => {
  keyboardRunning = !keyboardRunning;
  document.getElementById("keyboard-state").textContent = keyboardRunning ? "running" : "stopped";
  document.getElementById("keyboard-toggle").textContent = keyboardRunning ? "Stop Demo" : "Start Demo";
});
document.getElementById("keyboard-input").addEventListener("keydown", event => {
  if (!keyboardRunning) return;
  const feed = document.getElementById("keyboard-feed");
  const line = document.createElement("div");
  line.textContent = `${new Date().toLocaleTimeString()} demo-box ${event.key}`;
  feed.appendChild(line);
  feed.scrollTop = feed.scrollHeight;
});
document.getElementById("keyboard-clear").addEventListener("click", () => document.getElementById("keyboard-feed").replaceChildren());
document.getElementById("keyboard-export").addEventListener("click", () => {
  const text = [...document.getElementById("keyboard-feed").children].map(node => node.textContent).join("\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "keyboard-demo.txt";
  a.click();
  URL.revokeObjectURL(url);
});

document.querySelectorAll("[data-power]").forEach(button => button.addEventListener("click", async () => {
  const action = button.dataset.power;
  const decision = await openConfirm("Power control", `${action} requires a reason and audit log entry.`);
  if (!decision.ok) return;
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/power`, { method: "POST", body: JSON.stringify({ action, confirm: decision.confirm, reason: decision.reason }) });
}));

loadMachine().catch(alert);
loadAudit().catch(() => {});
loadFilesAndJobs().catch(() => {});
