# Demo Script

Target length: 5 to 7 minutes.

## Scene 1 - Login and Safety Scope (0:00-0:45)

1. Start API, relay, and fake agents:

   ```powershell
   py -3.12 main.py
   ```

   For real test machines, use `py -3.12 main.py --no-agents` on the main machine and run `py -3.12 client.py --server <MAIN_MACHINE_IP> --machine-id LAB-PC-REAL-01` on the test machine.

   Manual equivalent:

   ```powershell
   py -3.12 scripts/create_admin.py
   py -3.12 scripts/run_api.py
   py -3.12 scripts/run_relay.py
   py -3.12 scripts/run_3_fake_agents.py
   ```

2. Open `http://localhost:8000/admin/login`.
3. Login with `admin` / `admin123`.
4. State the scope: authorized lab demo, visible fake agents, no stealth, no credential collection.

## Scene 2 - Dashboard Overview (0:45-1:40)

1. Show `/admin/dashboard`.
2. Point out dashboard cards: online machines, stale/offline machines, active sessions, commands today.
3. Show recent audit logs.
4. Explain that the bright dashboard layout comes from the teacher `Topic01_Prototype.html` and now uses real API data.

## Scene 3 - Machines Page (1:40-2:25)

1. Open `/admin/machines`.
2. Search for `LAB-PC`.
3. Filter online machines.
4. Show hostname, machine id, OS, status, last seen, active controller, and Manage button.
5. Open `LAB-PC-01`.

## Scene 4 - Remote Shell and Screen (2:25-3:25)

1. Show the dark machine detail shell from `remote_control_web_prototype.html`.
2. Claim control.
3. Open Screen.
4. Start live view and show fake frames.
5. Capture/download the latest screen image if needed.
6. Mention the consent notice shown in the UI and by the agent console.

## Scene 5 - Apps, Processes, and Safety Controls (3:25-4:25)

1. Open Applications and refresh/list apps.
2. Start a fake app.
3. Stop an app through the confirmation modal.
4. Open Processes and refresh/list processes.
5. Explain protected processes: `lsass.exe`, `winlogon.exe`, `csrss.exe`, `services.exe`, `system`, `registry`.
6. State that protected process stops return `acl_denied` and are audited.

## Scene 6 - File Sandbox, Webcam, Keyboard Demo (4:25-5:45)

1. Open File Sandbox.
2. Upload a small `.txt` or `.py` file and dispatch it to the machine.
3. Show file metadata: filename, size, SHA-256, uploaded time, sandbox path, and job history.
4. Explain path traversal is blocked and the UI does not browse the full drive.
5. Open Webcam, check the consent box, start/stop webcam, and show the consent message.
6. Open Keyboard Demo, start it, type only inside the demo box, then clear/export the feed.
7. State that the browser waits for controller acknowledgment before forwarding key codes and never records global system keystrokes.

## Scene 7 - Power and Audit Logs (5:45-7:00)

1. Open Power.
2. Choose Restart or Shutdown.
3. Enter a reason and confirm.
4. Explain power remains demo-safe and does not actually shut down the machine.
5. Open Audit Logs.
6. Filter or refresh logs and show only events for the current `machine_id`.
7. End by showing README test commands and latest result: `py -3.12 -m pytest -q`.
## Fake Demo Recording Script (Real-Machine Pass)

1. Run `py -3.12 main.py`.
2. Log in at `/admin/login`.
3. Open `/admin/machines/LAB-PC-01`.
4. Claim control, list processes/applications, capture screen, start live screen, upload a small `.txt`, dispatch it, run a Python sandbox job, check webcam consent, and request demo-safe restart.
5. Open the audit panel and show machine-scoped logs for the same machine.

## Real Machine Demo Recording Script

1. On the server, run `py -3.12 scripts/check_server_network.py`, then `powershell -ExecutionPolicy Bypass -File scripts/start_server_windows.ps1`.
2. On the test machine, install optional deps and run `py -3.12 client.py --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --mode real`.
3. Confirm the visible agent banner is present on the test machine.
4. In the browser, claim control before sending actions.
5. Validate psutil process/app data, screen capture/live frames, sandbox file put/get, webcam consent/snapshot, and demo-safe power.
6. Only set `TELEPC_ENABLE_REAL_INPUT=true` for the short Keyboard Demo input segment, focus Notepad on the agent desktop, type inside the browser demo box, then unset it after recording.
