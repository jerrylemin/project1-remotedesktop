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

