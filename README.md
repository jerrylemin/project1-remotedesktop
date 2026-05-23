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

## Test

```powershell
python -m compileall .
pytest -q
```

Latest local result: `21 passed` with two FastAPI deprecation warnings for `on_event`.

## Demo Flow

1. Create admin with `python scripts/create_admin.py`.
2. Run API on port 8000 and relay on port 8001.
3. Run fake agent.
4. Log in to `/admin/login`.
5. Open Machines, select the fake machine, claim control, and view forwarded fake screen frames.
6. Use Processes, Applications, Files Sandbox, Audit Logs, and Danger Zone confirm controls.

