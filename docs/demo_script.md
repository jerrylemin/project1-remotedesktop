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

6. Multi-machine demo alternative:

   ```powershell
   python scripts/run_3_fake_agents.py
   ```

   This connects `LAB-PC-01`, `LAB-PC-02`, and `HOME-PC-01`.

7. Open `http://localhost:8000/admin/login`.
8. Login as `admin` / `admin123`.
9. Open Machines and show each fake machine with independent status.
10. Select one machine, claim control, start screen, and show frame forwarding.
11. Open another machine as observer and confirm input/commands require active controller lock.
12. Demonstrate audit logs filtered by event type and actor.
13. Upload a sandbox file, dispatch it to the selected machine, and show file metadata and job history.
14. Demonstrate Danger Zone confirmation with `CONFIRM`.
