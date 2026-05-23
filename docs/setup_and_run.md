# Setup And Run

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py --username admin --password admin123
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
```

Admin UI: `http://localhost:8000/admin/dashboard`

Default storage:

- SQLite database: `./telepc.db`
- Server artifacts: `./artifacts`
- Agent sandbox: `./sandbox`

Environment variables are documented in `.env.example`.

