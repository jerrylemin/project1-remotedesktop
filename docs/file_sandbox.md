# File Sandbox

Server-side:

- Uploads are size-limited.
- Allowed extensions: `.py`, `.ps1`, `.sh`, `.cmd`, `.txt`, `.csv`, `.json`.
- Filenames are generated UUID names.
- SHA256 is computed.
- Files are stored under `ARTIFACT_ROOT`, outside static public assets.

Agent-side:

```text
sandbox_root/<machine_id>/<job_id>/
```

Defenses:

- Reject absolute paths.
- Reject `../`, `./`, path separators, nested paths, and unsupported extensions.
- Resolve final paths and verify they remain inside the job sandbox.
- Use exclusive create to prevent overwrite.

Jobs:

- Runners are block-by-default via allowlist.
- Timeout is configurable.
- Output fields include command, cwd, stdout, stderr, exit_code, started_at, and finished_at.
- Machine detail UI shows sandbox files with filename, size, sha256, uploaded time, machine id, and dispatch job id.
- Job history shows command, status, exit code, stdout/stderr preview, and duration.

Endpoints:

- `GET /api/files/machines/{machine_id}`
- `GET /api/jobs/machines/{machine_id}/history`
