# Real agent migration plan

Date: 2026-06-01

## Current state

- The project has a consent-visible Python client entrypoint at `client.py`.
- Demo-safe mode is the default, and lab-real mode requires `--profile lab-real --confirm-real-mode TELEPC_LAB_AUTHORIZED`.
- The relay verifies registered machine secrets through the API.
- Sensitive actions use durable consent records and visible agent prompts, but the current prompt is console-based and not a native timed Windows popup.
- Fake agents and demo machine seeding still exist for local demos and tests.

## Migration target

- Production/admin views should show only machines connected through a real authorized agent.
- Fake agents should remain available only as explicit test/demo fixtures and should not be started by default production commands.
- The client should be distributed as one Windows executable: `dist/TelePCClient.exe`.
- The controlled machine should run a visible client process that connects outbound to the relay, asks for local consent before sensitive actions, and logs decisions.

## Packaging path

Build command:

```powershell
.\scripts\build_client_exe.ps1 -InstallPyInstaller
```

Repeat builds can omit dependency installation:

```powershell
.\scripts\build_client_exe.ps1
```

Expected artifact:

```text
dist\TelePCClient.exe
```

Implementation files:

- `scripts/package_client_exe.py`
- `scripts/build_client_exe.ps1`
- `tests/test_client_exe_packaging.py`

## Remaining strict-compliance work

1. Validate the rebuilt `TelePCClient.exe` on a physical Windows controlled machine.
2. Confirm native popup focus/topmost behavior across normal desktop windows.
3. Confirm `C:\Remote`, `D:\Remote`, and USB-drive `X:\Remote` discovery on real disks.
4. Confirm built-in and USB webcam enumeration with OpenCV on target hardware.
5. Keep the Keyboard Demo scoped and non-credential-collecting unless a separately approved lab key-capture design is documented.

## Build verification

2026-06-01:

- `.\scripts\build_client_exe.ps1` completed successfully.
- `Test-Path .\dist\TelePCClient.exe` returned `True`.
- `.\dist\TelePCClient.exe --help` exited successfully and displayed the expected client options.
