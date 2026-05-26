# UI Prototype Mapping

## Source Files

- `docs/teacher_prototypes/Topic01_Prototype.html`
- `docs/teacher_prototypes/remote_control_web_prototype.html`

## Topic01_Prototype.html

- Bright admin shell and sidebar groups -> `apps/api/templates/base.html`, `apps/api/templates/partials/sidebar.html`, `apps/api/static/css/app.css`, `apps/api/static/css/teacher_dashboard.css`.
- Dashboard cards for online machines, sessions, commands today, alerts -> `apps/api/templates/dashboard.html`, `apps/api/static/js/dashboard.js`, `GET /api/dashboard/summary`.
- Workstation list with hostname, IP/id, OS, status, Manage -> `apps/api/templates/dashboard.html`, `apps/api/templates/machines.html`, `apps/api/static/js/dashboard.js`, `apps/api/static/js/machines.js`, `GET /api/machines`.
- Recent audit logs -> `apps/api/templates/dashboard.html`, `apps/api/templates/audit.html`, `apps/api/static/js/audit.js`, `GET /api/dashboard/recent-audit`.
- Machine header fields and tabs -> `apps/api/templates/machine_detail.html`.
- Consent boxes and sandbox safety text -> `apps/api/templates/machine_detail.html`, `apps/api/static/css/teacher_remote_shell.css`.

## remote_control_web_prototype.html

- Dark connected shell topbar -> `apps/api/templates/machine_detail.html`, `apps/api/static/css/teacher_remote_shell.css`.
- Module sidebar: Applications, Processes, Screen, Keyboard Demo, Files, Webcam, Power -> `apps/api/templates/machine_detail.html`.
- Applications stats/table/start/stop -> `apps/api/static/js/machine_detail.js`, `GET /api/machines/{machine_id}/applications`, `POST /api/machines/{machine_id}/applications/start`, `POST /api/machines/{machine_id}/applications/stop`.
- Processes table and protected stop behavior -> `apps/api/static/js/machine_detail.js`, `POST /api/machines/{machine_id}/processes/{pid}/stop`, `apps/agent/commands.py`.
- Screen screenshot/live/capture/download UI -> `apps/api/templates/machine_detail.html`, `apps/api/static/js/ws_client.js`, `apps/api/static/js/machine_detail.js`, relay `/ws/admin`.
- Keyboard Demo feed/export/clear -> browser-only logic in `apps/api/static/js/machine_detail.js`.
- File Sandbox upload/dispatch/files/jobs -> `apps/api/static/js/files.js`, `apps/api/static/js/machine_detail.js`, existing file/job services plus `/api/machines/{machine_id}/sandbox/files` and `/api/machines/{machine_id}/sandbox/jobs`.
- Webcam consent/start/stop/snapshot -> `apps/api/static/js/machine_detail.js`, `POST /api/machines/{machine_id}/webcam/start`, `POST /api/machines/{machine_id}/webcam/stop`.
- Power confirm/reason/audit -> `apps/api/templates/partials/confirm_modal.html`, `apps/api/static/js/machine_detail.js`, `POST /api/machines/{machine_id}/power`.

## Notes

The prototype HTML was not copied as one static page. It was split into Jinja layout, partials, CSS, and JavaScript, with live data provided by FastAPI endpoints, the relay WebSocket, fake agents, audit logs, file sandbox, and job history.
