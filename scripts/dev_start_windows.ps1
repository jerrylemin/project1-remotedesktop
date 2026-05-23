$ErrorActionPreference = "Stop"
python scripts/create_admin.py
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "python scripts/run_api.py"
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "python scripts/run_relay.py"
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "python scripts/run_fake_agent.py"
Write-Host "TelePC API: http://localhost:8000/admin/dashboard"

