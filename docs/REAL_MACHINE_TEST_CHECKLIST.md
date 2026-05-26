# TelePC Real Machine Test Checklist

## Server Setup
- [ ] py -3.12 scripts/create_admin.py
- [ ] powershell -ExecutionPolicy Bypass -File scripts/start_server_windows.ps1
- [ ] Console shows "Listening on 0.0.0.0:8000" and "Listening on 0.0.0.0:8001"

## Client Setup (on test machine)
- [ ] py -3.12 -m pip install -r requirements.txt
- [ ] py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"
- [ ] py -3.12 client.py --server <SERVER_IP> --machine-id LAB-PC-REAL-01 --mode real
- [ ] Console shows "TelePC Agent running - consent visible"

## Browser Validation (each step = expected result)
- [ ] Login /admin/login -> redirects to /admin/dashboard
- [ ] Anonymous /admin/dashboard -> redirects to /admin/login
- [ ] Machine list shows LAB-PC-REAL-01 as online
- [ ] Click Manage -> /admin/machines/LAB-PC-REAL-01 loads
- [ ] Claim Control -> button disabled for others
- [ ] List Processes -> real PIDs from psutil
- [ ] List Applications -> real running apps
- [ ] Start notepad -> Notepad.exe opens on test machine
- [ ] Stop notepad -> process terminated
- [ ] Capture Screen -> JPEG displayed in UI
- [ ] Start Live Screen (5 FPS) -> frames updating
- [ ] Enable Full Control -> click on screen -> mouse moves on test machine
- [ ] Type text -> appears in Notepad on test machine
- [ ] Upload file (test.txt) -> artifact created
- [ ] Dispatch file -> sandbox/LAB-PC-REAL-01/.../test.txt exists
- [ ] Download sandbox file -> bytes returned correctly
- [ ] Run sandbox job (python -c "print('ok')") -> stdout: ok
- [ ] Check consent box -> Start Webcam -> frame appears
- [ ] Webcam Snapshot -> artifact saved
- [ ] Power Restart (demo-safe) -> demo_safe: true in response
- [ ] Audit Logs -> all actions show machine_id=LAB-PC-REAL-01
- [ ] View Machine B audit -> no Machine A logs visible

## Known Safe Limitations
- Real input requires TELEPC_ENABLE_REAL_INPUT=true (off by default)
- Real power requires TELEPC_ENABLE_REAL_POWER=true (off by default)
- Webcam requires opencv-python installed on test machine
- Screen capture requires mss installed on test machine
