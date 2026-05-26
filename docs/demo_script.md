# Demo Script

1. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Create demo admin:

   ```powershell
   python scripts/create_admin.py
   ```

3. Start API:

   ```powershell
   python scripts/run_api.py
   ```

4. Start relay:

   ```powershell
   python scripts/run_relay.py
   ```

5. Start three fake agents:

   ```powershell
   python scripts/run_3_fake_agents.py
   ```

   This connects `LAB-PC-01`, `LAB-PC-02`, and `HOME-PC-01`.

6. Open `http://localhost:8000/admin/login`.
7. Login as `admin` / `admin123`.
8. Show the bright Dashboard cards: online machines, stale/offline machines, active screen sessions, commands today, alerts, recent audit logs.
9. Open Machines and show search/filter, status pills, last seen, active controller, and Manage buttons.
10. Select each fake machine once to show the dark remote shell and the machine-specific header.
11. Claim control on one machine and start Screen live view; show fake frames forwarded by the relay.
12. Open Audit Logs for that machine and refresh; confirm only that machine's events are visible.
13. Open Processes, refresh the list, and show that protected process names would render as Protected and are denied by the API.
14. Open Applications, list applications, start a fake app, and stop an app with confirmation.
15. Open File Sandbox, upload a file, dispatch it to the machine, and show artifact metadata, SHA-256, sandbox path, and job history.
16. Open Webcam, explain the consent checkbox, check it, start/stop webcam, and show the audit event.
17. Open Keyboard Demo, start demo, type inside the text box, export/clear the local demo feed, and state it does not capture global keystrokes.
18. Open Power, choose Restart or Shutdown, enter a reason, confirm, and show the resulting audit log.
