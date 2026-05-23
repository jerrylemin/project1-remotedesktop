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

5. Start fake agent:

   ```powershell
   python scripts/run_fake_agent.py
   ```

6. Open `http://localhost:8000/admin/login`.
7. Login as `admin` / `admin123`.
8. Open Machines and select the fake machine.
9. Claim control, start screen, and show frame forwarding.
10. Demonstrate process/app list, file upload/dispatch, job creation, audit tab, and Danger Zone confirmation.

