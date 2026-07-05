# TelePC Remote Desktop Lab

Hướng dẫn triển khai hai máy bằng tiếng Việt: [`docs/HUONG_DAN_SU_DUNG_SERVER_CLIENT.md`](docs/HUONG_DAN_SU_DUNG_SERVER_CLIENT.md).

TelePC is a lab remote desktop control system for authorized machines. It uses a FastAPI admin/API server, a WebSocket relay, and a consent-visible Python client agent.

## Safety Scope

- Authorized lab/admin use only.
- No stealth behavior, hidden persistence, antivirus bypass, or credential collection.
- Screen, webcam, Keylogger Lab Module, file, and power actions are consent-visible and auditable.
- The Keylogger Lab Module is for authorized lab demonstration only: it starts after local Yes, has a short TTL, stays in memory by default, supports stop/export consent, and redacts sensitive-window contexts.
- Remote file browsing is limited to discovered existing `X:\Remote` roots on the controlled machine; whole-drive browsing and path traversal are blocked.
- Protected system processes such as `lsass.exe`, `winlogon.exe`, `csrss.exe`, `services.exe`, `system`, and `registry` cannot be stopped through the UI/API.

## Strict Lab Control Path

Production machine lists show enrolled connected clients only. Build `dist\TelePCClient.exe`, create an enroll token, and run the client on an authorized lab machine to connect it through the relay.

Every control action that affects the controlled machine must pass authentication, authorization, machine access checks, exact command-payload consent, local consent, and audit logging. Process kill and webcam stop are explicitly consent-gated, along with application control, screen capture/live screen, file listing/download, webcam enumeration/start, Keylogger Lab Module start/stop/export, and restart/shutdown.

## Teacher Prototype UI

The admin UI now applies the teacher prototype as real FastAPI/Jinja pages instead of static HTML:

- `Topic01_Prototype.html` -> bright dashboard, machine list, security/audit navigation.
- `remote_control_web_prototype.html` -> dark per-machine remote shell with Applications, Processes, Screen, Files, Webcam, Keylogger Lab Module, Power, and Audit Logs modules.

The UI is split across `apps/api/templates`, `apps/api/templates/partials`, `apps/api/static/css`, and `apps/api/static/js`, and reads data from the existing API, relay WebSocket, connected client agents, and audit/file/job services.

## Setup

Use Python 3.11+.

```powershell
python -m pip install -r requirements.txt
```

On Windows, if the default `python` is Python 3.10, use the launcher explicitly:

```powershell
py -3.12 -m pip install -r requirements.txt
```

`main.py` initializes the database and securely prompts for the first admin password when no admin exists. It never creates or prints a default password.

## Run

Production-safe startup uses one file and one terminal. It initializes the database, creates the first admin interactively when needed, listens on all LAN interfaces, tries to open Windows Firewall for TCP `8000` and `8001`, starts the API, and starts the relay. It does not start demo agents:

```powershell
python main.py
```

Windows launcher equivalent:

```powershell
py -3.12 main.py
```

Then open `http://localhost:8000/admin/dashboard`.

The console prints the LAN URL and a ready-to-copy `client.py` command for test machines. Press `Ctrl+C` in that terminal to stop everything.
If the API or relay is already running on the selected ports, `main.py` reuses it and starts only the missing pieces.

Manual startup, separate terminals:

Open two terminals:

```powershell
python scripts/run_api.py
python scripts/run_relay.py
```

Windows launcher equivalent:

```powershell
py -3.12 scripts/run_api.py
py -3.12 scripts/run_relay.py
```

Then open `http://localhost:8000/admin/dashboard`.

Use enrolled real clients for the machine list. The production UI shows only connected, enrolled client machines.

## Connect a Test Machine

On the main/controller machine, run:

```powershell
py -3.12 main.py
```

`main.py` listens on the LAN and tries to open Windows Firewall for TCP `8000` and `8001`. If Windows asks for permission, allow Python on the private network. The main console prints the LAN IP. You can also find it manually:

```powershell
ipconfig
```

On each authorized test machine, install dependencies and run the client:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"
py -3.12 client.py --server <MAIN_MACHINE_IP> --machine-id LAB-PC-REAL-01 --token <REGISTERED_MACHINE_SECRET>
```

If the main machine is still starting, `client.py` waits and retries instead of exiting immediately.

Keep the client console visible and open. The machine will appear in `/admin/machines`; click Manage from the main machine to control it. Real input and real power are enabled automatically in real mode, while consent, controller authorization, audit logging, and the `X:\Remote` file boundary remain enforced.

## Auth Flow

Admin login sets an HttpOnly session cookie. Browser JavaScript does not store the long-lived JWT in `localStorage`; it asks `POST /api/ws-ticket` for a short-lived WebSocket ticket and sends that ticket to the relay. The relay validates tickets through the API using `INTERNAL_API_SECRET`.

## Demo Flow

1. Run `python main.py`; on the first run, enter and confirm the admin password.
2. Log in at `/admin/login` with username `admin` and that password.
3. Build and run `TelePCClient.exe` or `client.py` on an authorized lab machine.
4. Open `/admin/dashboard` and review online machines, active sessions, commands today, alerts, and recent audit logs.
5. Open `/admin/machines`, search/filter machines, then click Manage.
6. Claim control in `/admin/machines/{machine_id}`.
7. Use Screen to start live frame viewing or capture/download the latest image after local consent.
8. Use Processes and Applications; protected processes are blocked and process kill requires local consent.
9. Browse only discovered `X:\Remote` folders or dispatch sandbox files, then review audit/job history.
10. Enumerate/select Webcam devices and start or stop Webcam only after local consent, then review per-machine Audit Logs.

## Windows Real Agent

Real mode is the default client mode and is intended only for authorized lab machines. Demo mode is development-only and requires both `--mode demo` and `TELEPC_ALLOW_DEMO=true`.

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

Latest local result: `221 passed`.
## Real Machine Completion Pass

### Quick Start

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 main.py
```

Open `http://localhost:8000/admin/login`, sign in with the seeded admin, then connect an authorized client machine with `client.py` or `TelePCClient.exe`.

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
| Screen capture | `mss` or `Pillow` ImageGrab | Clear unavailable error if missing in real mode |
| Processes/applications | `psutil` | Clear unavailable error if missing in real mode |
| Webcam | `opencv-python` | Clear unavailable error if missing in real mode |
| Real input | `pyautogui` | Enabled automatically in real mode; disabled during tests/demo-safe execution |
| Real power | Windows built-ins | Enabled automatically in real mode; consent, reason, delay, and pytest guards remain |

### Known Limitations

- Physical Windows validation is still required for real screen FPS, real input, webcam, and power commands.
- Real input and real power are enabled by default for authorized real-mode machines.
- Power `lock` and `cancel` require the audit confirmation checkbox but do not require a reason. `restart` and `shutdown` require a reason of at least 5 characters.
- File dispatch supports inline bytes up to 512 KB; larger files are prepared for signed download URL handoff.

Webcam live tuning for real agents:

```powershell
$env:TELEPC_WEBCAM_FPS="30"              # 1..30
$env:TELEPC_WEBCAM_JPEG_QUALITY="25"    # 25..90
$env:TELEPC_WEBCAM_WIDTH="640"
$env:TELEPC_WEBCAM_HEIGHT="360"
```

Real input and real power are enabled automatically by normal real-mode Client and Server startup. The legacy explicit helper remains available for compatible lab scripts:

```powershell
.\scripts\run_lab_real_client.ps1 --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --token <REGISTERED_MACHINE_SECRET>
```

Equivalent direct launch:

```powershell
python client.py --profile lab-real --confirm-real-mode TELEPC_LAB_AUTHORIZED --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --token <REGISTERED_MACHINE_SECRET>
```

Build a one-file Windows client executable:

```powershell
.\scripts\build_client_exe.ps1 -InstallPyInstaller
```

The expected artifact is:

```text
dist\TelePCClient.exe
```

Use `-InstallPyInstaller` the first time only; later builds can run `.\scripts\build_client_exe.ps1`.

Keylogger Lab Module validation:

```powershell
.\scripts\run_lab_real_client.ps1 --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --token <REGISTERED_MACHINE_SECRET>
```

In the browser, claim control, open Keylogger Lab Module, click `Start Key Capture`, and approve the visible local popup on the controlled machine. TelePC stores mock/test events in memory during tests, requires a TTL and stop path, and redacts keys when the active window title suggests credentials or payment. Export requires separate consent.

## Security and Consent Model

- Relay agent websocket auth verifies the machine id and machine secret against the registered machine record.
- Disabled or unknown machines cannot connect.
- Teacher access is machine-grant scoped; admins can access all machines, auditors remain read-only.
- Sensitive actions create an exact payload-bound consent request and are blocked until the visible controlled-machine agent approves it.
- Screen frames do not stream on websocket connection; live screen starts only after a consent-approved command.
- Real-mode startup sets `TELEPC_ENABLE_REAL_INPUT=true`, `TELEPC_ENABLE_REAL_POWER=true`, and `TELEPC_REAL_MODE_CONFIRMED=TELEPC_LAB_AUTHORIZED` automatically; tests remain forced into safe mocked behavior.

## Final Validation Status

Automated gates pass: compile, Ruff, pytest, HTTP smoke, and EXE build. The current strict score is capped at `96/100` until a physical Windows lab run saves the required evidence under `artifacts/physical_validation/`. Use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_physical_lab_validation.ps1
```

## Submission Cleanup

Create a clean submission archive under `artifacts/submission/`:

```powershell
.\scripts\prepare_submission.ps1
```

```bash
sh scripts/prepare_submission.sh
```

The cleanup scripts remove caches, local `.env`, local SQLite databases, and generated local artifacts from the archive while keeping source, tests, docs, and `.env.example`.
