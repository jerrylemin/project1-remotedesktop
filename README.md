# TelePC Remote Desktop Lab

TelePC is a lab/demo remote desktop control system for authorized machines. It uses a FastAPI admin/API server, a WebSocket relay, and a consent-visible Python agent. Fake mode is the default demo path and does not control the local machine.

## Safety Scope

- Authorized lab/admin use only.
- No stealth behavior, hidden persistence, antivirus bypass, or credential collection.
- Agent startup prints visible control/consent status.
- Key input handling records metadata only.
- Dangerous actions require explicit confirmation and audit logging.

## Setup

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py
```

Default demo admin:

- Username: `admin`
- Password: `admin123`

## Run

Open three terminals:

```powershell
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
```

Then open `http://localhost:8000/admin/dashboard`.

Run three fake agents for the multi-machine demo:

```powershell
python scripts/run_3_fake_agents.py
```

This connects `LAB-PC-01`, `LAB-PC-02`, and `HOME-PC-01` through the relay.

## Auth Flow

Admin login sets an HttpOnly session cookie. Browser JavaScript does not store the long-lived JWT in `localStorage`; it asks `POST /api/ws-ticket` for a short-lived WebSocket ticket and sends that ticket to the relay. The relay validates tickets through the API using `INTERNAL_API_SECRET`.

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

- Use Python 3.11.
- Run in a visible console; the agent prints consent/control status.
- Optional dependency failures do not crash the agent; commands return clear errors and are auditable as `command_failed`.
- Stop cleanly with `Ctrl+C`.

## Test

```powershell
python -m compileall .
pytest -q
```

Latest local result: `35 passed` with no FastAPI deprecation warnings.

## Demo Flow

1. Create admin with `python scripts/create_admin.py`.
2. Run API on port 8000 and relay on port 8001.
3. Run fake agent.
4. Or run `python scripts/run_3_fake_agents.py` to show multiple machines.
5. Log in to `/admin/login`.
6. Open Machines, select the fake machine, claim control, and view forwarded fake screen frames.
7. Use Processes, Applications, Files Sandbox, Audit Logs, and Danger Zone confirm controls.
