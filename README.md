# TelePC Remote Desktop Lab

TelePC is a lab/demo remote desktop control system for authorized machines. It uses a FastAPI admin/API server, a WebSocket relay, and a consent-visible Python agent. Fake mode is the default demo path and does not control the local machine.

## Safety Scope

- Authorized lab/admin use only.
- No stealth behavior, hidden persistence, antivirus bypass, or credential collection.
- Screen, webcam, keyboard demo, file, and power actions are consent-visible and auditable.
- Keyboard Demo only records keys typed in the browser demo box, not global system keystrokes.
- Files move through the sandbox only; whole-drive browsing and path traversal are blocked.
- Protected system processes such as `lsass.exe`, `winlogon.exe`, `csrss.exe`, `services.exe`, `system`, and `registry` cannot be stopped through the UI/API.

## Teacher Prototype UI

The admin UI now applies the teacher prototype as real FastAPI/Jinja pages instead of static HTML:

- `Topic01_Prototype.html` -> bright dashboard, machine list, security/audit navigation.
- `remote_control_web_prototype.html` -> dark per-machine remote shell with Applications, Processes, Screen, Files, Webcam, Keyboard Demo, Power, and Audit Logs modules.

The UI is split across `apps/api/templates`, `apps/api/templates/partials`, `apps/api/static/css`, and `apps/api/static/js`, and reads data from the existing API, relay WebSocket, fake agent, and audit/file/job services.

## Setup

Use Python 3.11+.

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py
```

On Windows, if the default `python` is Python 3.10, use the launcher explicitly:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/create_admin.py
```

Default demo admin:

- Username: `admin`
- Password: `admin123`

## Run

Fast demo startup, one terminal. By default this listens on all LAN interfaces, tries to open Windows Firewall for TCP `8000` and `8001`, seeds the admin, starts the API, starts the relay, and starts three fake demo agents:

```powershell
python main.py
```

Windows launcher equivalent:

```powershell
py -3.12 main.py
```

Then open `http://localhost:8000/admin/dashboard`.

For a main/controller machine that will control separate test machines, run:

```powershell
py -3.12 main.py --no-agents
```

The console prints the LAN URL and a ready-to-copy `client.py` command for test machines. Press `Ctrl+C` in that terminal to stop everything.
If the API or relay is already running on the selected ports, `main.py` reuses it and starts only the missing pieces.

Manual startup, separate terminals:

Open three terminals:

```powershell
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
```

Windows launcher equivalent:

```powershell
py -3.12 scripts/run_api.py
py -3.12 scripts/run_relay.py
py -3.12 scripts/run_fake_agent.py
```

Then open `http://localhost:8000/admin/dashboard`.

Run three fake agents for the multi-machine demo:

```powershell
python scripts/run_3_fake_agents.py
```

or:

```powershell
py -3.12 scripts/run_3_fake_agents.py
```

This connects `LAB-PC-01`, `LAB-PC-02`, and `HOME-PC-01` through the relay.

## Connect a Test Machine

On the main/controller machine, run:

```powershell
py -3.12 main.py --no-agents
```

`main.py` listens on the LAN and tries to open Windows Firewall for TCP `8000` and `8001`. If Windows asks for permission, allow Python on the private network. The main console prints the LAN IP. You can also find it manually:

```powershell
ipconfig
```

On each authorized test machine, install dependencies and run the client:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"
py -3.12 client.py --server <MAIN_MACHINE_IP> --machine-id LAB-PC-REAL-01
```

If the main machine is still starting, `client.py` waits and retries instead of exiting immediately.

For fake/demo mode on a test machine:

```powershell
py -3.12 client.py --server <MAIN_MACHINE_IP> --machine-id LAB-PC-TEST-01 --mode fake
```

Keep the client console visible and open. The machine will appear in `/admin/machines`; click Manage from the main machine to control it. The real client remains consent-visible, uses sandbox-only file operations, and keeps power actions demo-safe.

## Auth Flow

Admin login sets an HttpOnly session cookie. Browser JavaScript does not store the long-lived JWT in `localStorage`; it asks `POST /api/ws-ticket` for a short-lived WebSocket ticket and sends that ticket to the relay. The relay validates tickets through the API using `INTERNAL_API_SECRET`.

## Demo Flow

1. Start API, relay, and `python scripts/run_3_fake_agents.py`.
2. Log in at `/admin/login` with `admin` / `admin123`.
3. Open `/admin/dashboard` and review online machines, active sessions, commands today, alerts, and recent audit logs.
4. Open `/admin/machines`, search/filter machines, then click Manage.
5. Claim control in `/admin/machines/{machine_id}`.
6. Use Screen to start live frame viewing or capture/download the latest image.
7. Use Processes and Applications; protected processes are blocked and audited.
8. Upload and dispatch a sandbox file, then review sandbox files and job history.
9. Start Webcam only after checking the consent box.
10. Use Power controls with confirmation and a reason, then review per-machine Audit Logs.

## Windows Real Agent

Real mode is optional and intended only for authorized lab machines.

```powershell
python -m pip install -r requirements.txt
python -m pip install "mss>=9.0" "psutil>=6.0" "pynput>=1.7" "opencv-python>=4.10"
$env:AGENT_MODE="real"
$env:MACHINE_ID="<machine-id>"
$env:MACHINE_TOKEN="<machine-secret>"
python scripts/run_agent.py
```

Notes:

- Use Python 3.11+.
- Run in a visible console; the agent prints consent/control status.
- Optional dependency failures do not crash the agent; commands return clear errors and are auditable as `command_failed`.
- Stop cleanly with `Ctrl+C`.

## Test

```powershell
python -m compileall .
pytest -q
```

Windows launcher equivalent:

```powershell
py -3.12 -m compileall .
py -3.12 -m pytest -q
```

Latest local result with Python 3.12: `42 passed`.
## Real Machine Completion Pass

### Quick Start (Fake)

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/create_admin.py
py -3.12 main.py
```

Open `http://localhost:8000/admin/login`, sign in with the seeded admin, then use the fake lab agents for screen frames, process/app lists, file sandbox, webcam consent flow, and demo-safe power actions.

### Real Machine Setup

Server machine:

```powershell
py -3.12 scripts/check_server_network.py
powershell -ExecutionPolicy Bypass -File scripts/start_server_windows.ps1
```

Test machine:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7" "pyautogui>=0.9"
py -3.12 client.py --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --mode real
```

LAN firewall: open inbound TCP `8000` and `8001` on the server only. Test machines need outbound access only. Verify from a test machine with:

```powershell
Test-NetConnection <SERVER_IP> -Port 8000
Test-NetConnection <SERVER_IP> -Port 8001
```

### Optional Real-Agent Dependencies

| Capability | Package | Safe default |
| --- | --- | --- |
| Screen capture | `mss` or `Pillow` ImageGrab | Fake JPEG frames |
| Processes/applications | `psutil` | Fake grouped rows |
| Webcam | `opencv-python` | Consent-gated fake frame/status |
| Real input | `pyautogui` | Disabled unless `TELEPC_ENABLE_REAL_INPUT=true` |
| Real power | Windows built-ins | Demo-safe unless `TELEPC_ENABLE_REAL_POWER=true` |

### Known Limitations

- Physical Windows validation is still required for real screen FPS, real input, webcam, and power commands.
- Real input and real power are intentionally opt-in environment-gated features.
- File dispatch supports inline bytes up to 512 KB; larger files are prepared for signed download URL handoff.
