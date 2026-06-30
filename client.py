from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import importlib.util
import os
import platform
import re
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from apps.agent.config import AgentSettings  # noqa: E402
from apps.agent.consent import require_consent_banner  # noqa: E402
from apps.agent.ws_client import run_agent  # noqa: E402

REAL_MODE_CONFIRMATION = "TELEPC_LAB_AUTHORIZED"


@dataclass
class ClientConfig:
    server: str = "127.0.0.1"
    api_url: str | None = None
    relay_url: str | None = None
    api_port: int = 8000
    relay_port: int = 8001
    machine_id: str = ""
    token: str = ""
    mode: str = "real"
    profile: str | None = None
    confirm_real_mode: str | None = None
    sandbox_root: str = "./sandbox"
    skip_port_check: bool = False
    connect_timeout: int = 0


def default_machine_id() -> str:
    raw = platform.node() or socket.gethostname() or "telepc-client"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-")
    return cleaned or "telepc-client"


def tcp_open(host: str, port: int, timeout: float = 3.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def endpoint_host_port(url: str, fallback_host: str, fallback_port: int) -> tuple[str, int]:
    parsed = urlparse(url)
    return parsed.hostname or fallback_host, parsed.port or fallback_port


def wait_for_tcp(label: str, host: str, port: int, timeout_seconds: int) -> None:
    start = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        if tcp_open(host, port):
            print(f"[telepc-client] {label} reachable at {host}:{port}", flush=True)
            return
        elapsed = time.monotonic() - start
        if timeout_seconds > 0 and elapsed >= timeout_seconds:
            raise SystemExit(
                f"{label} is still unreachable at {host}:{port}. "
                "On the main machine run `py -3.12 main.py --no-agents` and allow firewall ports 8000/8001."
            )
        print(f"[telepc-client] waiting for {label} {host}:{port} ... attempt {attempt}", flush=True)
        time.sleep(2)


def warn_missing_real_dependencies() -> None:
    checks = {
        "mss": "screen capture",
        "psutil": "process/application control",
        "cv2": "webcam",
        "pynput": "optional input provider",
    }
    missing = [f"{module} ({purpose})" for module, purpose in checks.items() if importlib.util.find_spec(module) is None]
    if missing:
        print("[telepc-client] optional real-agent dependencies missing:", flush=True)
        for item in missing:
            print(f"  - {item}", flush=True)
        print("[telepc-client] install on the test machine with:", flush=True)
        print('  py -3.12 -m pip install "mss>=9.0" "psutil>=6.0" "opencv-python>=4.10" "pynput>=1.7"', flush=True)
        print("[telepc-client] the client will still connect, but missing modules return clear command errors.", flush=True)


def parse_client_args(argv: list[str] | None = None) -> ClientConfig:
    parser = argparse.ArgumentParser(description="Connect this test machine to a TelePC controller.")
    parser.add_argument("--server", default="127.0.0.1", help="IP/hostname of the main TelePC machine.")
    parser.add_argument("--api-url", default=None, help="Full API URL, overrides --server/--api-port.")
    parser.add_argument("--relay-url", default=None, help="Full relay WebSocket URL, overrides --server/--relay-port.")
    parser.add_argument("--api-port", type=int, default=8000, help="API port on the main machine.")
    parser.add_argument("--relay-port", type=int, default=8001, help="Relay port on the main machine.")
    parser.add_argument("--machine-id", default=default_machine_id(), help="Name shown in the Machines page.")
    parser.add_argument("--token", default=os.getenv("MACHINE_TOKEN", ""), help="Registered machine secret sent to relay. Keep non-empty.")
    parser.add_argument("--mode", choices=["demo", "fake", "real"], default="real", help="Use real lab providers by default. Demo requires TELEPC_ALLOW_DEMO=true.")
    parser.add_argument("--profile", choices=["lab-real"], default=None, help="Explicit profile for authorized lab real mode.")
    parser.add_argument("--confirm-real-mode", default=None, help="Required confirmation phrase for real lab input/power.")
    parser.add_argument("--sandbox-root", default="./sandbox", help="Local sandbox root on this test machine.")
    parser.add_argument("--skip-port-check", action="store_true", help="Skip TCP checks before connecting.")
    parser.add_argument("--connect-timeout", type=int, default=0, help="Seconds to wait for main machine. 0 waits forever.")
    args = parser.parse_args(argv)
    mode = "demo" if args.mode == "fake" else args.mode
    if mode == "demo" and os.getenv("TELEPC_ALLOW_DEMO", "false").lower() not in {"1", "true", "yes"}:
        raise SystemExit("Demo mode requires TELEPC_ALLOW_DEMO=true.")
    return ClientConfig(
        server=args.server,
        api_url=args.api_url,
        relay_url=args.relay_url,
        api_port=args.api_port,
        relay_port=args.relay_port,
        machine_id=args.machine_id,
        token=args.token,
        mode=mode,
        profile=args.profile,
        confirm_real_mode=args.confirm_real_mode,
        sandbox_root=args.sandbox_root,
        skip_port_check=args.skip_port_check,
        connect_timeout=args.connect_timeout,
    )


def apply_lab_real_profile(config: ClientConfig) -> ClientConfig:
    if config.profile != "lab-real":
        return config
    if os.getenv("CI", "").lower() in {"1", "true", "yes"}:
        raise SystemExit("CI must never enable TelePC lab-real mode.")
    config.mode = "real"
    return config


def require_real_mode_confirmation(config: ClientConfig) -> None:
    real_env_requested = any(
        os.getenv(name, "").lower() == "true"
        for name in ("TELEPC_ENABLE_REAL_INPUT", "TELEPC_ENABLE_REAL_POWER")
    )
    if config.profile != "lab-real" and not real_env_requested:
        return
    if config.confirm_real_mode != REAL_MODE_CONFIRMATION:
        raise SystemExit(
            "Real mode refused. Safe usage: python client.py --profile lab-real "
            f"--confirm-real-mode {REAL_MODE_CONFIRMATION}"
        )


def set_real_mode_environment(config: ClientConfig) -> None:
    if config.profile != "lab-real":
        os.environ.pop("TELEPC_ENABLE_REAL_INPUT", None)
        os.environ.pop("TELEPC_ENABLE_REAL_POWER", None)
        os.environ.pop("TELEPC_REAL_MODE_CONFIRMED", None)
        return
    os.environ["TELEPC_ENABLE_REAL_INPUT"] = "true"
    os.environ["TELEPC_ENABLE_REAL_POWER"] = "true"
    os.environ["TELEPC_REAL_MODE_CONFIRMED"] = REAL_MODE_CONFIRMATION


def parse_args() -> ClientConfig:
    config = parse_client_args()
    config = apply_lab_real_profile(config)
    require_real_mode_confirmation(config)
    set_real_mode_environment(config)
    return config


async def main_async() -> None:
    args = parse_args()
    api_url = args.api_url or f"http://{args.server}:{args.api_port}"
    relay_url = args.relay_url or f"ws://{args.server}:{args.relay_port}"

    if not args.token:
        raise SystemExit("--token must be non-empty")

    if args.mode == "real":
        warn_missing_real_dependencies()

    if not args.skip_port_check:
        api_host, api_port = endpoint_host_port(api_url, args.server, args.api_port)
        relay_host, relay_port = endpoint_host_port(relay_url, args.server, args.relay_port)
        wait_for_tcp("API", api_host, api_port, args.connect_timeout)
        wait_for_tcp("relay", relay_host, relay_port, args.connect_timeout)

    settings = AgentSettings(
        relay_url=relay_url,
        api_url=api_url,
        machine_token=args.token,
        machine_id=args.machine_id,
        sandbox_root=Path(args.sandbox_root),
        require_consent=True,
        agent_mode="real" if args.mode == "real" else "fake",
    )
    settings.sandbox_root.mkdir(parents=True, exist_ok=True)

    require_consent_banner(settings.machine_id, real_mode=settings.agent_mode == "real")
    print(f"[telepc-client] API: {api_url}", flush=True)
    print(f"[telepc-client] Relay: {relay_url}", flush=True)
    print(f"[telepc-client] Machine ID: {settings.machine_id}", flush=True)
    print("[telepc-client] Keep this console open. Press Ctrl+C to disconnect.", flush=True)
    await run_agent(settings)


def main() -> int:
    try:
        asyncio.run(main_async())
        return 0
    except KeyboardInterrupt:
        print("\n[telepc-client] disconnected by user", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
