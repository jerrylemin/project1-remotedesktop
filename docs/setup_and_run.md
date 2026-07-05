# Setup And Run

```powershell
python -m pip install -r requirements.txt
python main.py
```

`main.py` initializes the database, prompts securely for the first admin password, starts API and relay, opens the LAN ports when possible, and stops everything together with `Ctrl+C`. For a real two-machine deployment, follow `docs/HUONG_DAN_SU_DUNG_SERVER_CLIENT.md`.

Admin UI: `http://localhost:8000/admin/dashboard`

Optional multi-machine fake demo:

```powershell
python scripts/run_3_fake_agents.py
```

Real Windows agent:

Real input and real power are enabled automatically for authorized real-mode runs. Consent and audit controls remain active.

```powershell
python -m pip install "mss>=9.0" "psutil>=6.0" "pynput>=1.7" "opencv-python>=4.10"
$env:AGENT_MODE="real"
$env:MACHINE_ID="<machine-id>"
$env:MACHINE_TOKEN="<machine-secret>"
python scripts/run_agent.py
```

Build one-file Windows client executable:

```powershell
.\scripts\build_client_exe.ps1 -InstallPyInstaller
```

Expected artifact:

```text
dist\TelePCClient.exe
```

Default storage:

- SQLite database: `./telepc.db`
- Server artifacts: `./artifacts`
- Agent sandbox: `./sandbox`

Environment variables are documented in `.env.example`.
