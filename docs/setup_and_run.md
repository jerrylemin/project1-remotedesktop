# Setup And Run

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py --username admin --password admin123
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
```

Admin UI: `http://localhost:8000/admin/dashboard`

Multi-machine fake demo:

```powershell
python scripts/run_3_fake_agents.py
```

Real Windows agent:

```powershell
python -m pip install "mss>=9.0" "psutil>=6.0" "pynput>=1.7" "opencv-python>=4.10"
$env:AGENT_MODE="real"
$env:MACHINE_ID="<machine-id>"
$env:MACHINE_TOKEN="<machine-secret>"
python scripts/run_agent.py
```

Default storage:

- SQLite database: `./telepc.db`
- Server artifacts: `./artifacts`
- Agent sandbox: `./sandbox`

Environment variables are documented in `.env.example`.
