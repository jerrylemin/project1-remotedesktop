const machineId = window.MACHINE_ID;
const protectedProcesses = new Set(["lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"]);
let currentSessionId = null;
let lastFrameAt = 0;
let keyboardRunning = false;
let lastFrameMeta = { width: 640, height: 360 };

const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c]));
const fmtDate = value => value ? new Date(value).toLocaleString() : "never";

const wsClient = new TelepcWsClient(machineId, {
  onFrame: frame => {
    if (frame?.type === "webcam_frame") {
      renderWebcamFrame(frame);
      return;
    }
    const jpeg = typeof frame === "string" ? frame : (frame.data || frame.jpeg_b64);
    if (!jpeg) return;
    if (typeof frame === "object") lastFrameMeta = { width: frame.width || 640, height: frame.height || 360 };
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

function renderWebcamFrame(frame) {
  const jpeg = frame.data || frame.jpeg_b64;
  if (!jpeg) return;
  document.getElementById("webcam-preview").innerHTML = `<img alt="Webcam frame" src="data:image/jpeg;base64,${esc(jpeg)}">`;
  document.getElementById("webcam-status").textContent = frame.fps ? `live ${frame.fps} fps` : "live";
}

async function jsonFetch(url, options = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `${url} failed`);
  return res.json();
}

function requireClaim(message = "Claim control before sending this command.") {
  if (!currentSessionId) throw new Error(message);
}

async function apiCommand(url, options = {}, { requireControl = true } = {}) {
  if (requireControl) requireClaim();
  const response = await jsonFetch(url, options);
  if (response.command) {
    await wsClient.connect({ control: true });
    wsClient.sendCommand(response.command);
  }
  await loadAudit();
  return response;
}

async function requestLocalConsent(commandType, reason) {
  requireClaim("Claim control before requesting local consent.");
  const consent = await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/consent-requests`, {
    method: "POST",
    body: JSON.stringify({ command_type: commandType, reason, ttl_seconds: 300 }),
  });
  await wsClient.connect({ control: true });
  const response = await wsClient.sendCommandAwait({ action: "consent_request", request: consent });
  const result = response.payload?.result || {};
  const decision = result.decision || "denied";
  await jsonFetch(`/api/consent-requests/${encodeURIComponent(consent.id)}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, decided_by: `agent:${machineId}` }),
  });
  await loadAudit();
  if (decision !== "approved") throw new Error(`${commandType} consent denied`);
  return consent;
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
  if (panel === "webcam") loadWebcamDevices().catch(alert);
  if (panel === "audit") loadAudit().catch(alert);
}

function handleWsResult(msg) {
  if (msg.type === "error") {
    alert(msg.payload?.detail || "Relay error");
    return;
  }
  const payload = msg.payload || {};
  if (payload.ok === false) {
    alert(payload.error || "Command failed");
    return;
  }
  const result = payload.result || payload;
  if (result.processes) renderProcesses(result.processes);
  if (result.applications) renderApplications(result.applications);
  const webcamFrame = result.webcam_frame || (result.type === "webcam_frame" ? result : null);
  if (webcamFrame) {
    renderWebcamFrame(webcamFrame);
  }
  if (result.webcam) {
    document.getElementById("webcam-status").textContent = result.webcam;
    if (!webcamFrame) {
      document.getElementById("webcam-preview").textContent = result.webcam === "started" ? "Webcam active with consent" : "Camera preview starts only after consent.";
    }
  }
  if (result.event && result.key_event_count) {
    const state = result.error || (result.demo_safe ? "demo-safe: TELEPC_ENABLE_REAL_INPUT is not true" : "real input sent");
    appendKeyboardFeed(result.event, state);
    document.getElementById("keyboard-state").textContent = state;
  }
  if (result.action && result.demo_safe) document.getElementById("power-result").textContent = `${result.action} accepted for demo-safe agent flow`;
  loadAudit().catch(() => {});
}

function appendKeyboardFeed(eventName, detail) {
  const feed = document.getElementById("keyboard-feed");
  const line = document.createElement("div");
  line.textContent = `${new Date().toLocaleTimeString()} ${eventName} ${detail}`;
  feed.appendChild(line);
  feed.scrollTop = feed.scrollHeight;
}

function renderApplications(apps) {
  const normalized = apps.map(app => ({
    appKey: app.app_key || String(app.name || "").toLowerCase(),
    name: app.display_name || app.name || app.command || "unknown",
    status: app.running ? "running" : (app.installed ? "stopped" : "missing"),
    cpu: app.cpu_percent ?? app.cpu ?? "0",
  }));
  document.getElementById("apps-badge").textContent = normalized.length;
  document.getElementById("apps-running").textContent = normalized.filter(app => String(app.status).toLowerCase() === "running").length;
  document.getElementById("apps-high-cpu").textContent = normalized.filter(app => Number(app.cpu) >= 20).length;
  document.getElementById("apps-background").textContent = normalized.filter(app => String(app.status).toLowerCase() !== "running").length;
  document.getElementById("apps-table").innerHTML = normalized.map(app => {
    const running = String(app.status).toLowerCase() === "running";
    return `<tr><td>${esc(app.name)}</td><td><span class="run-badge ${running ? "run" : "idle"}">${esc(app.status)}</span></td><td>${esc(app.cpu)}%</td><td><button class="action-btn ${running ? "kill" : "start"}" data-app="${esc(app.appKey)}" data-app-action="${running ? "stop" : "start"}">${running ? "Stop" : "Start"}</button></td></tr>`;
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

async function loadWebcamDevices() {
  const response = await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/devices`);
  const devices = response.command ? [] : (response.webcam_devices || []);
  const select = document.getElementById("webcam-device");
  if (select && !select.children.length) {
    select.innerHTML = `<option value="camera-0">Camera 0</option>`;
  }
}

async function loadAudit() {
  const filter = document.getElementById("audit-event-filter")?.value || "";
  const suffix = filter ? `?event_type=${encodeURIComponent(filter)}` : "";
  const rows = await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/audit${suffix}`);
  const html = rows.map(row => `<div class="audit-item"><strong>${esc(row.event_type)}</strong><small>${esc(row.actor_type)} · ${fmtDate(row.created_at)} · ${esc(row.machine_id || "")}</small><span>${esc(row.summary)}</span><pre class="metadata-preview">${esc(JSON.stringify(row.metadata_json, null, 2))}</pre></div>`).join("") || `<div class="audit-item">No audit events for this machine.</div>`;
  document.getElementById("audit-list").innerHTML = html;
  document.getElementById("recent-audit").innerHTML = html;
}

function openConfirm(title, message, { reasonRequired = false } = {}) {
  const modal = document.getElementById("confirm-modal");
  const reasonField = document.getElementById("confirm-reason");
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-message").textContent = message;
  reasonField.value = "";
  reasonField.required = reasonRequired;
  reasonField.placeholder = reasonRequired ? "Reason for audit log, at least 5 characters" : "Optional reason for audit log";
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
    await requestLocalConsent("APPLICATION_START", `Start ${name}`);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/start`, { method: "POST", body: JSON.stringify({ name, confirm: true }) });
  } else {
    const decision = await openConfirm("Stop application", `Stop ${name}?`);
    if (decision.ok) {
      await requestLocalConsent("APPLICATION_STOP", `Stop ${name}`);
      await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/stop`, { method: "POST", body: JSON.stringify({ name, confirm: decision.confirm }) });
    }
  }
});

document.getElementById("process-table").addEventListener("click", async event => {
  const button = event.target.closest("[data-pid]");
  if (!button) return;
  const decision = await openConfirm("Stop process", `Stop PID ${button.dataset.pid} (${button.dataset.process})?`);
  if (!decision.ok) return;
  await requestLocalConsent("PROCESS_KILL", `Stop PID ${button.dataset.pid} (${button.dataset.process})`);
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/processes/${encodeURIComponent(button.dataset.pid)}/stop`, { method: "POST", body: JSON.stringify({ name: button.dataset.process, confirm: decision.confirm }) });
});

document.getElementById("start-screen").addEventListener("click", async () => {
  await requestLocalConsent("LIVE_SCREEN", "Start live screen view");
  await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/screen/start`, { method: "POST", body: JSON.stringify({ mode: "live", consent: true }) });
  document.getElementById("screen-mode-label").textContent = "Live mode";
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
  await requestLocalConsent("SCREENSHOT", "Capture current screen");
  await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/screen/capture`, { method: "POST", body: JSON.stringify({ mode: "screenshot", consent: true }) });
  await loadAudit();
});
document.getElementById("screen-fps").addEventListener("change", async event => {
  requireClaim("Claim control before changing screen FPS.");
  await wsClient.connect({ control: true });
  wsClient.sendCommand({ action: "set_screen_fps", fps: Number(event.target.value) });
});

document.getElementById("full-control-toggle").addEventListener("change", event => {
  document.getElementById("full-control-label").textContent = event.target.checked ? "Full Control ON - Requires active claim" : "Full Control OFF";
});

async function sendInput(eventName, event) {
  if (!document.getElementById("full-control-toggle").checked || !currentSessionId) return;
  const image = document.getElementById("remote-screen");
  const rect = image.getBoundingClientRect();
  const x = Math.round((event.offsetX ?? (event.clientX - rect.left)) * lastFrameMeta.width / Math.max(1, rect.width));
  const y = Math.round((event.offsetY ?? (event.clientY - rect.top)) * lastFrameMeta.height / Math.max(1, rect.height));
  try {
    await wsClient.connect({ control: true });
    wsClient.send("input_event", { action: "input_event", event: eventName, x, y, delta_y: event.deltaY });
  } catch (error) {
    alert(error.message || error);
  }
}

["mousemove", "mousedown", "mouseup", "click", "dblclick", "wheel"].forEach(name => {
  document.getElementById("remote-screen").addEventListener(name, event => sendInput(name.replace("mouse", "mouse_"), event));
});
document.getElementById("upload-file").addEventListener("click", async () => {
  try {
    requireClaim("Claim control before dispatching files to the agent sandbox.");
    const artifact = await TelepcFiles.uploadArtifact(document.getElementById("file-input"));
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/file-dispatch`, { method: "POST", body: JSON.stringify({ artifact_id: artifact.artifact_id }) });
    await loadFilesAndJobs();
    await loadAudit();
  } catch (error) {
    alert(error.message || error);
  }
});

document.getElementById("webcam-start").addEventListener("click", async () => {
  try {
    if (!document.getElementById("webcam-consent").checked) throw new Error("Check webcam consent before starting the camera.");
    const deviceId = document.getElementById("webcam-device")?.value || "camera-0";
    await requestLocalConsent("WEBCAM_START", "Start webcam preview");
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/start`, { method: "POST", body: JSON.stringify({ consent: true, device_id: deviceId }) });
  } catch (error) {
    alert(error.message || error);
  }
});
document.getElementById("webcam-stop").addEventListener("click", async () => {
  try {
    await requestLocalConsent("WEBCAM_STOP", "Stop webcam preview");
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/stop`, { method: "POST", body: JSON.stringify({ consent: true }) });
  } catch (error) {
    alert(error.message || error);
  }
});
document.getElementById("webcam-snapshot").addEventListener("click", () => {
  try {
    if (!document.getElementById("webcam-consent").checked) throw new Error("Check webcam consent before taking a snapshot.");
    requestLocalConsent("WEBCAM_START", "Take webcam snapshot")
      .then(() => apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/snapshot`, { method: "POST", body: JSON.stringify({ consent: true }) }))
      .catch(alert);
  } catch (error) {
    alert(error.message || error);
  }
});

document.getElementById("keyboard-toggle").addEventListener("click", async () => {
  if (!keyboardRunning && !currentSessionId) {
    alert("Claim control before starting real keyboard input.");
    return;
  }
  if (!keyboardRunning) {
    try {
      await requestLocalConsent("KEY_INPUT", "Keyboard Demo input forwarding");
    } catch (error) {
      alert(error.message || error);
      return;
    }
  }
  keyboardRunning = !keyboardRunning;
  document.getElementById("keyboard-state").textContent = keyboardRunning ? "running" : "stopped";
  document.getElementById("keyboard-toggle").textContent = keyboardRunning ? "Stop Real Input" : "Start Real Input";
});

async function sendKeyboardDemoEvent(eventName, event) {
  if (!keyboardRunning) return;
  if (!currentSessionId) {
    alert("Claim control before sending keyboard input.");
    keyboardRunning = false;
    document.getElementById("keyboard-state").textContent = "stopped";
    document.getElementById("keyboard-toggle").textContent = "Start Real Input";
    return;
  }
  event.preventDefault();
  try {
    await wsClient.connect({ control: true });
    wsClient.send("input_event", { action: "input_event", event: eventName, code: event.code });
    appendKeyboardFeed(eventName, event.code);
  } catch (error) {
    appendKeyboardFeed(eventName, error.message || error);
    alert(error.message || error);
  }
}

document.getElementById("keyboard-input").addEventListener("keydown", event => sendKeyboardDemoEvent("key_down", event));
document.getElementById("keyboard-input").addEventListener("keyup", event => sendKeyboardDemoEvent("key_up", event));
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
  try {
    const action = button.dataset.power;
    const needsReason = action === "restart" || action === "shutdown";
    const decision = await openConfirm("Power control", needsReason ? `${action} requires confirmation and a reason of at least 5 characters.` : `${action} requires confirmation and will be audited.`, { reasonRequired: needsReason });
    if (!decision.ok) return;
    if (!decision.confirm) throw new Error("Check the audit confirmation box before sending a power action.");
    if (needsReason && decision.reason.trim().length < 5) throw new Error("Power restart/shutdown requires a reason of at least 5 characters.");
    if (needsReason) await requestLocalConsent(`POWER_${action.toUpperCase()}`, `Power ${action}: ${decision.reason}`);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/power`, { method: "POST", body: JSON.stringify({ action, confirm: true, reason: decision.reason }) });
  } catch (error) {
    alert(error.message || error);
  }
}));

loadMachine().catch(alert);
loadAudit().catch(() => {});
loadFilesAndJobs().catch(() => {});
