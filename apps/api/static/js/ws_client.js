class TelepcWsClient {
  constructor(machineId, { onFrame, onResult, onStatus } = {}) {
    this.machineId = machineId;
    this.onFrame = onFrame || (() => {});
    this.onResult = onResult || (() => {});
    this.onStatus = onStatus || (() => {});
    this.ws = null;
    this.role = "observer";
    this.roleWaiters = [];
    this.resultWaiters = new Map();
  }

  async ticket() {
    const res = await fetch("/api/ws-ticket", { method: "POST" });
    if (!res.ok) throw new Error("Unable to issue WebSocket ticket");
    return (await res.json()).ws_ticket;
  }

  send(type, payload = {}, sessionId = null) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) throw new Error("WebSocket is not connected");
    const msgId = crypto.randomUUID();
    this.ws.send(JSON.stringify({ type, msg_id: msgId, ts: new Date().toISOString(), machine_id: this.machineId, session_id: sessionId, payload }));
    return msgId;
  }

  async connect({ control = false } = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (control && this.role !== "controller") await this.subscribe(true);
      return;
    }
    this.onStatus("reconnecting");
    const wsTicket = await this.ticket();
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    const url = `${scheme}://${location.hostname}:8001/ws/admin`;
    this.ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Relay connection timed out")), 5000);
      this.ws.addEventListener("open", () => {
        this.ws.send(JSON.stringify({ type: "auth", msg_id: crypto.randomUUID(), ts: new Date().toISOString(), machine_id: null, session_id: null, payload: { ws_ticket: wsTicket } }));
        clearTimeout(timer);
        resolve();
      }, { once: true });
      this.ws.addEventListener("error", () => reject(new Error("Relay connection failed")), { once: true });
    });
    this.ws.addEventListener("message", event => this.handle(JSON.parse(event.data)));
    this.ws.addEventListener("close", () => {
      this.rejectResultWaiters(new Error("Relay disconnected"));
      this.onStatus("offline");
    });
    await this.subscribe(control);
  }

  async subscribe(control = false) {
    const waitForController = control ? this.waitForRole("controller") : null;
    this.send("subscribe_machine", { control });
    if (waitForController) await waitForController;
  }

  waitForRole(role, timeoutMs = 5000) {
    if (this.role === role) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const waiter = { role, resolve, reject, timer: null };
      waiter.timer = setTimeout(() => {
        this.roleWaiters = this.roleWaiters.filter(item => item !== waiter);
        reject(new Error(`WebSocket did not become ${role}`));
      }, timeoutMs);
      this.roleWaiters.push(waiter);
    });
  }

  resolveRoleWaiters() {
    const ready = this.roleWaiters.filter(waiter => waiter.role === this.role);
    this.roleWaiters = this.roleWaiters.filter(waiter => waiter.role !== this.role);
    ready.forEach(waiter => {
      clearTimeout(waiter.timer);
      waiter.resolve();
    });
  }

  handle(msg) {
    if (msg.type === "ack" && msg.payload?.role) {
      this.role = msg.payload.role;
      this.onStatus(this.role === "controller" ? "online" : "observer");
      this.resolveRoleWaiters();
    }
    if (msg.type === "error") {
      const detail = msg.payload?.detail || "Relay error";
      this.roleWaiters.forEach(waiter => {
        clearTimeout(waiter.timer);
        waiter.reject(new Error(detail));
      });
      this.roleWaiters = [];
    }
    if (msg.type === "frame" && (msg.payload?.jpeg_b64 || msg.payload?.data)) this.onFrame(msg.payload);
    if (msg.type === "command_result" || msg.type === "error" || msg.type === "job_status") {
      const waiter = msg.session_id ? this.resultWaiters.get(msg.session_id) : null;
      if (waiter) {
        clearTimeout(waiter.timer);
        this.resultWaiters.delete(msg.session_id);
        waiter.resolve(msg);
      }
      this.onResult(msg);
    }
  }

  sendCommand(command, commandId = null) {
    return this.send("command", command, commandId);
  }

  sendCommandAwait(command, timeoutMs = 120000) {
    return new Promise((resolve, reject) => {
      const commandId = crypto.randomUUID();
      const waiter = { resolve, reject, timer: null };
      waiter.timer = setTimeout(() => {
        this.resultWaiters.delete(commandId);
        reject(new Error("Timed out waiting for agent response"));
      }, timeoutMs);
      this.resultWaiters.set(commandId, waiter);
      try {
        this.sendCommand(command, commandId);
      } catch (error) {
        clearTimeout(waiter.timer);
        this.resultWaiters.delete(commandId);
        reject(error);
      }
    });
  }

  rejectResultWaiters(error) {
    this.resultWaiters.forEach(waiter => {
      clearTimeout(waiter.timer);
      waiter.reject(error);
    });
    this.resultWaiters.clear();
  }

  close() {
    this.rejectResultWaiters(new Error("Relay closed"));
    this.ws?.close();
    this.ws = null;
    this.role = "observer";
    this.onStatus("offline");
  }
}

window.TelepcWsClient = TelepcWsClient;
