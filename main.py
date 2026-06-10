from __future__ import annotations

import argparse
import asyncio
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from apps.api.seed import seed_admin  # noqa: E402


def local_check_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::", ""} else host


def local_lan_ips() -> list[str]:
    ips: set[str] = set()
    try:
        hostname = socket.gethostname()
        for item in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = item[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except socket.gaierror:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if not ip.startswith("127."):
                ips.add(ip)
    except OSError:
        pass
    return sorted(ips)


def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, label: str, timeout: float = 20.0) -> None:
    check_host = local_check_host(host)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_is_open(check_host, port):
            print(f"[telepc] {label} ready on {check_host}:{port}", flush=True)
            return
        time.sleep(0.5)
    raise RuntimeError(f"{label} did not open {check_host}:{port} within {timeout:.0f}s")


def ensure_windows_firewall_rule(name: str, port: int) -> None:
    if platform.system().lower() != "windows":
        return
    command = [
        "netsh",
        "advfirewall",
        "firewall",
        "add",
        "rule",
        f"name={name}",
        "dir=in",
        "action=allow",
        "protocol=TCP",
        f"localport={port}",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    output = f"{result.stdout}\n{result.stderr}".lower()
    if result.returncode == 0 or "already exists" in output:
        print(f"[telepc] firewall rule ready for TCP {port}", flush=True)
    else:
        print(f"[telepc] firewall auto-open skipped for TCP {port}. Run PowerShell as Administrator if LAN clients cannot connect.", flush=True)


def start_child(name: str, command: list[str], env: dict[str, str] | None = None) -> subprocess.Popen:
    print(f"[telepc] starting {name}: {' '.join(command)}", flush=True)
    child_env = os.environ.copy()
    child_env.update(env or {})
    return subprocess.Popen([sys.executable, *command], cwd=ROOT, env=child_env)


def stop_children(children: list[tuple[str, subprocess.Popen]]) -> None:
    for name, process in reversed(children):
        if process.poll() is None:
            print(f"[telepc] stopping {name}", flush=True)
            process.terminate()
    deadline = time.monotonic() + 8
    for name, process in reversed(children):
        if process.poll() is not None:
            continue
        remaining = max(0.1, deadline - time.monotonic())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            print(f"[telepc] force stopping {name}", flush=True)
            process.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the complete TelePC demo stack.")
    parser.add_argument("--host", default="0.0.0.0", help="Host used by API and relay. Default accepts LAN clients.")
    parser.add_argument("--api-port", type=int, default=8000, help="API port.")
    parser.add_argument("--relay-port", type=int, default=8001, help="Relay port.")
    parser.add_argument("--username", default="admin", help="Demo admin username to seed.")
    parser.add_argument("--password", default="admin123", help="Demo admin password to seed.")
    parser.add_argument("--no-agents", action="store_true", help="Deprecated alias for the production-safe default.")
    parser.add_argument("--demo-agents", action="store_true", help="Start fake demo agents and seed fake demo machines.")
    parser.add_argument("--skip-firewall", action="store_true", help="Do not try to add Windows Firewall rules.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    children: list[tuple[str, subprocess.Popen]] = []

    try:
        local_host = local_check_host(args.host)
        api_already_running = port_is_open(local_host, args.api_port)
        relay_already_running = port_is_open(local_host, args.relay_port)

        if not args.skip_firewall:
            ensure_windows_firewall_rule(f"TelePC API {args.api_port}", args.api_port)
            ensure_windows_firewall_rule(f"TelePC Relay {args.relay_port}", args.relay_port)

        print("[telepc] preparing database and admin user", flush=True)
        asyncio.run(seed_admin(args.username, args.password, include_demo_machines=args.demo_agents))
        print(f"[telepc] admin ready: {args.username} / {args.password}", flush=True)

        api_url = f"http://{local_host}:{args.api_port}"
        relay_url = f"ws://{local_host}:{args.relay_port}"

        if api_already_running:
            print(f"[telepc] API already running on {local_host}:{args.api_port}; reusing it", flush=True)
        else:
            api = start_child("api", ["-m", "uvicorn", "apps.api.main:app", "--host", args.host, "--port", str(args.api_port)])
            children.append(("api", api))
            wait_for_port(args.host, args.api_port, "API")

        if relay_already_running:
            print(f"[telepc] Relay already running on {local_host}:{args.relay_port}; reusing it", flush=True)
        else:
            relay = start_child(
                "relay",
                ["-m", "uvicorn", "apps.relay.main:app", "--host", args.host, "--port", str(args.relay_port)],
                env={"API_URL": api_url},
            )
            children.append(("relay", relay))
            wait_for_port(args.host, args.relay_port, "Relay")

        if args.demo_agents and not args.no_agents:
            agents = start_child("fake agents", ["scripts/run_3_fake_agents.py"], env={"API_URL": api_url, "RELAY_URL": relay_url})
            children.append(("fake agents", agents))

        print("", flush=True)
        print("[telepc] TelePC is running.", flush=True)
        print(f"[telepc] Open http://localhost:{args.api_port}/admin/login", flush=True)
        for ip in local_lan_ips():
            print(f"[telepc] LAN URL: http://{ip}:{args.api_port}/admin/login", flush=True)
            print(f"[telepc] Test machine command: py -3.12 client.py --server {ip} --machine-id LAB-PC-REAL-01", flush=True)
        print(f"[telepc] Login: {args.username} / {args.password}", flush=True)
        print("[telepc] Press Ctrl+C to stop TelePC.", flush=True)
        print("", flush=True)

        while True:
            for name, process in children:
                code = process.poll()
                if code is not None:
                    raise RuntimeError(f"{name} exited unexpectedly with code {code}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[telepc] shutdown requested", flush=True)
        return 0
    except Exception as exc:
        print(f"[telepc] startup failed: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        stop_children(children)


if __name__ == "__main__":
    raise SystemExit(main())
