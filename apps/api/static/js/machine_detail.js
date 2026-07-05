const machineId = window.MACHINE_ID;
const protectedProcesses = new Set(["lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"]);
let currentSessionId = null;
let lastFrameAt = 0;
let keyboardRunning = false;
let lastFrameMeta = { width: 640, height: 360 };
let remoteRoots = [];
let selectedRemoteRoot = null;
let selectedRemoteRelativePath = "";
let keyloggerSessionId = null;
let keyloggerExpiryTimer = null;

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

async function apiCommandAwait(url, options = {}, { requireControl = true } = {}) {
  if (requireControl) requireClaim();
  const response = await jsonFetch(url, options);
  if (!response.command) return response;
  await wsClient.connect({ control: true });
  const msg = await wsClient.sendCommandAwait(response.command);
  await loadAudit();
  const payload = msg.payload || {};
  if (payload.ok === false) throw new Error(payload.error || "Command failed");
  return payload.result || payload;
}

async function requestLocalConsent(commandType, reason, commandPayload = {}) {
  requireClaim("Claim control before requesting local consent.");
  const consent = await jsonFetch(`/api/machines/${encodeURIComponent(machineId)}/consent-requests`, {
    method: "POST",
    body: JSON.stringify({ command_type: commandType, reason, command_payload: commandPayload, ttl_seconds: 300 }),
  });
  await wsClient.connect({ control: true });
  const response = await wsClient.sendCommandAwait({ action: "consent_request", request: consent });
  const result = response.payload?.result || {};
  const decision = result.decision || "denied";
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
  if (panel === "files") {
    loadFilesAndJobs().catch(alert);
    loadRemoteRoots().catch(() => {});
  }
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
  if (result.session && result.session.session_id) {
    keyloggerSessionId = result.session.session_id;
    appendKeyboardFeed("keylogger", `${result.session.status} · events ${result.event_count ?? 0}`);
  }
  if (result.events) {
    result.events.forEach(event => appendKeyboardFeed(event.event_type, `${event.key_name}${event.redacted ? " redacted" : ""}`));
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

function renderRemoteRoots(folders) {
  remoteRoots = folders || [];
  selectedRemoteRoot = remoteRoots[0]?.root_path || null;
  selectedRemoteRelativePath = "";
  document.getElementById("remote-root-list").innerHTML = remoteRoots.map(folder => `<button class="btn ghost" data-remote-root="${esc(folder.root_path)}">${esc(folder.drive_letter)}:\\Remote</button>`).join("") || `<div class="stack-item">No whitelisted remote folders found on this machine.</div>`;
  document.getElementById("remote-files-output").replaceChildren();
  document.getElementById("remote-files-up").disabled = true;
}

function renderRemoteFiles(files) {
  document.getElementById("remote-files-up").disabled = !selectedRemoteRelativePath;
  document.getElementById("remote-files-output").innerHTML = files.map(file => {
    const isDir = file.entry_type === "directory";
    return `<div class="stack-item"><strong>${esc(file.name)}</strong><small>${esc(file.entry_type)} · ${file.size_bytes ?? "-"} bytes · ${fmtDate(file.modified_at)}</small><button class="btn ghost" data-remote-path="${esc(file.relative_path)}" data-remote-action="${isDir ? "open" : "download"}">${isDir ? "Open" : "Download"}</button></div>`;
  }).join("") || `<div class="stack-item">No files in this whitelisted folder.</div>`;
}

async function loadRemoteRoots() {
  const result = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/remote-files/folders`);
  renderRemoteRoots(result.allowed_folders || []);
}

async function listRemoteFiles(relativePath = selectedRemoteRelativePath) {
  if (!selectedRemoteRoot) throw new Error("No whitelisted remote folder selected.");
  const payload = { root_path: selectedRemoteRoot, relative_path: relativePath, consent: true };
  await requestLocalConsent("FILE_LIST", `List ${selectedRemoteRoot}\\${relativePath || ""}`, payload);
  const result = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/remote-files/list`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  selectedRemoteRelativePath = relativePath;
  renderRemoteFiles(result.files || []);
}

async function downloadRemoteFile(relativePath) {
  if (!selectedRemoteRoot) throw new Error("No whitelisted remote folder selected.");
  const payload = { root_path: selectedRemoteRoot, relative_path: relativePath, consent: true };
  await requestLocalConsent("FILE_DOWNLOAD", `Download ${selectedRemoteRoot}\\${relativePath}`, payload);
  const result = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/remote-files/download`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const bytes = Uint8Array.from(atob(result.content_base64 || ""), c => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes]));
  const a = document.createElement("a");
  a.href = url;
  a.download = result.filename || "telepc-download.bin";
  a.click();
  URL.revokeObjectURL(url);
}

async function loadWebcamDevices() {
  document.getElementById("webcam-status").textContent = "loading devices";
  await requestLocalConsent("WEBCAM_ENUMERATE", "List available webcam devices", {});
  const response = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/webcam/devices`);
  const devices = response.webcam_devices || [];
  const select = document.getElementById("webcam-device");
  const start = document.getElementById("webcam-start");
  select.innerHTML = devices.map(device => `<option value="${esc(device.device_id)}">${esc(device.name || device.device_id)} (${esc(device.backend || "camera")})</option>`).join("");
  if (!devices.length) {
    document.getElementById("webcam-status").textContent = "no webcam found";
    start.disabled = true;
  } else {
    document.getElementById("webcam-status").textContent = "device list loaded";
    start.disabled = false;
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
document.getElementById("load-remote-roots").addEventListener("click", () => loadRemoteRoots().catch(alert));
document.getElementById("remote-files-up").addEventListener("click", () => {
  const parts = selectedRemoteRelativePath.split(/[\\/]/).filter(Boolean);
  parts.pop();
  listRemoteFiles(parts.join("\\")).catch(alert);
});
document.getElementById("remote-root-list").addEventListener("click", event => {
  const button = event.target.closest("[data-remote-root]");
  if (!button) return;
  selectedRemoteRoot = button.dataset.remoteRoot;
  selectedRemoteRelativePath = "";
  listRemoteFiles("").catch(alert);
});
document.getElementById("remote-files-output").addEventListener("click", event => {
  const button = event.target.closest("[data-remote-action]");
  if (!button) return;
  const path = button.dataset.remotePath;
  if (button.dataset.remoteAction === "open") listRemoteFiles(path).catch(alert);
  if (button.dataset.remoteAction === "download") downloadRemoteFile(path).catch(alert);
});

document.getElementById("apps-table").addEventListener("click", async event => {
  const button = event.target.closest("[data-app-action]");
  if (!button) return;
  const action = button.dataset.appAction;
  const name = button.dataset.app;
  if (action === "start") {
    const payload = { name, confirm: true };
    await requestLocalConsent("APPLICATION_START", `Start ${name}`, payload);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/start`, { method: "POST", body: JSON.stringify(payload) });
  } else {
    const decision = await openConfirm("Stop application", `Stop ${name}?`);
    if (decision.ok) {
      const payload = { name, confirm: decision.confirm };
      await requestLocalConsent("APPLICATION_STOP", `Stop ${name}`, payload);
      await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/applications/stop`, { method: "POST", body: JSON.stringify(payload) });
    }
  }
});

document.getElementById("process-table").addEventListener("click", async event => {
  const button = event.target.closest("[data-pid]");
  if (!button) return;
  const decision = await openConfirm("Stop process", `Stop PID ${button.dataset.pid} (${button.dataset.process})?`);
  if (!decision.ok) return;
  const payload = { pid: Number(button.dataset.pid), name: button.dataset.process, confirm: decision.confirm };
  await requestLocalConsent("PROCESS_KILL", `Stop PID ${button.dataset.pid} (${button.dataset.process})`, payload);
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/processes/${encodeURIComponent(button.dataset.pid)}/stop`, { method: "POST", body: JSON.stringify({ name: payload.name, confirm: payload.confirm }) });
});

document.getElementById("start-screen").addEventListener("click", async () => {
  const payload = { mode: "live", consent: true };
  await requestLocalConsent("LIVE_SCREEN_START", "Start live screen view", payload);
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/screen/start`, { method: "POST", body: JSON.stringify(payload) });
  document.getElementById("screen-mode-label").textContent = "Live mode";
  await loadAudit();
});
document.getElementById("stop-screen").addEventListener("click", async () => {
  const payload = { mode: "live", consent: true };
  await requestLocalConsent("LIVE_SCREEN_STOP", "Stop live screen view", payload);
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/screen/stop`, { method: "POST", body: JSON.stringify(payload) });
  document.getElementById("screen-mode-label").textContent = "Screenshot mode";
  document.getElementById("fps-label").textContent = "0 fps";
  await loadAudit();
});
document.getElementById("capture-screen").addEventListener("click", async () => {
  const payload = { mode: "screenshot", consent: true };
  await requestLocalConsent("SCREENSHOT", "Capture current screen", payload);
  await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/screen/capture`, { method: "POST", body: JSON.stringify(payload) });
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
    const payload = { consent: true, device_id: deviceId };
    await requestLocalConsent("WEBCAM_START", "Start webcam preview", payload);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/start`, { method: "POST", body: JSON.stringify(payload) });
  } catch (error) {
    alert(error.message || error);
  }
});
document.getElementById("webcam-stop").addEventListener("click", async () => {
  try {
    const payload = { consent: true };
    await requestLocalConsent("WEBCAM_STOP", "Stop webcam preview", payload);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/stop`, { method: "POST", body: JSON.stringify(payload) });
  } catch (error) {
    alert(error.message || error);
  }
});
document.getElementById("webcam-snapshot").addEventListener("click", () => {
  try {
    if (!document.getElementById("webcam-consent").checked) throw new Error("Check webcam consent before taking a snapshot.");
    const payload = { consent: true, device_id: null };
    requestLocalConsent("WEBCAM_START", "Take webcam snapshot", payload)
      .then(() => apiCommand(`/api/machines/${encodeURIComponent(machineId)}/webcam/snapshot`, { method: "POST", body: JSON.stringify(payload) }))
      .catch(alert);
  } catch (error) {
    alert(error.message || error);
  }
});

document.getElementById("keyboard-toggle").addEventListener("click", async () => {
  if (!keyboardRunning && !currentSessionId) {
    alert("Claim control before starting keyboard capture.");
    return;
  }
  if (!keyboardRunning) {
    try {
      keyloggerSessionId = crypto.randomUUID();
      const payload = {
        session_id: keyloggerSessionId,
        ttl_seconds: Number(document.getElementById("keylogger-ttl").value || 60),
        consent: true,
      };
      await requestLocalConsent("KEYLOGGER_START", "Start keyboard capture on this computer for lab demonstration", payload);
      const result = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/keylogger/start`, { method: "POST", body: JSON.stringify(payload) });
      clearTimeout(keyloggerExpiryTimer);
      const expiresAt = Date.parse(result.session?.expires_at || "");
      keyloggerExpiryTimer = setTimeout(() => {
        keyboardRunning = false;
        document.getElementById("keyboard-state").textContent = "expired";
        document.getElementById("keyboard-toggle").textContent = "Start Key Capture";
      }, Math.max(0, (Number.isFinite(expiresAt) ? expiresAt - Date.now() : payload.ttl_seconds * 1000)));
    } catch (error) {
      alert(error.message || error);
      return;
    }
  } else if (keyloggerSessionId) {
    try {
      const payload = { session_id: keyloggerSessionId, consent: true };
      await requestLocalConsent("KEYLOGGER_STOP", "Stop keyboard capture", payload);
      await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/keylogger/stop`, { method: "POST", body: JSON.stringify(payload) });
      clearTimeout(keyloggerExpiryTimer);
    } catch (error) {
      alert(error.message || error);
      return;
    }
  }
  keyboardRunning = !keyboardRunning;
  document.getElementById("keyboard-state").textContent = keyboardRunning ? "running" : "stopped";
  document.getElementById("keyboard-toggle").textContent = keyboardRunning ? "Stop Key Capture" : "Start Key Capture";
});

document.getElementById("keyboard-clear").addEventListener("click", () => document.getElementById("keyboard-feed").replaceChildren());
document.getElementById("keyboard-export").addEventListener("click", async () => {
  try {
    if (!keyloggerSessionId) throw new Error("No key capture session to export.");
    const payload = { session_id: keyloggerSessionId, consent: true };
    await requestLocalConsent("KEYLOGGER_EXPORT", "Export key capture events", payload);
    const result = await apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/keylogger/${encodeURIComponent(keyloggerSessionId)}/export`, { method: "POST", body: JSON.stringify(payload) });
    const bytes = Uint8Array.from(atob(result.content_base64 || ""), c => c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = result.filename || "keylogger-lab.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    alert(error.message || error);
  }
});

document.querySelectorAll("[data-power]").forEach(button => button.addEventListener("click", async () => {
  try {
    const action = button.dataset.power;
    const needsReason = action === "restart" || action === "shutdown";
    const decision = await openConfirm("Power control", needsReason ? `${action} requires confirmation and a reason of at least 5 characters.` : `${action} requires confirmation and will be audited.`, { reasonRequired: needsReason });
    if (!decision.ok) return;
    if (!decision.confirm) throw new Error("Check the audit confirmation box before sending a power action.");
    if (needsReason && decision.reason.trim().length < 5) throw new Error("Power restart/shutdown requires a reason of at least 5 characters.");
    const payload = { action, confirm: true, reason: decision.reason };
    if (needsReason) await requestLocalConsent(`POWER_${action.toUpperCase()}`, `Power ${action}: ${decision.reason}`, payload);
    await apiCommand(`/api/machines/${encodeURIComponent(machineId)}/power`, { method: "POST", body: JSON.stringify(payload) });
  } catch (error) {
    alert(error.message || error);
  }
}));

loadMachine().catch(alert);
loadAudit().catch(() => {});
loadFilesAndJobs().catch(() => {});
