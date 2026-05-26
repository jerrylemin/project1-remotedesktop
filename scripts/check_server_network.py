from __future__ import annotations

import socket


def lan_ips() -> list[str]:
    ips: set[str] = set()
    hostname = socket.gethostname()
    for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
        ip = info[4][0]
        if not ip.startswith("127."):
            ips.add(ip)
    return sorted(ips)


def can_bind(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


def main() -> None:
    ips = lan_ips()
    print("LAN IPs:", ", ".join(ips) if ips else "none detected")
    for port in (8000, 8001):
        print(f"Port {port} bind available: {can_bind(port)}")
    server_ip = ips[0] if ips else "<SERVER_IP>"
    print(f"Test machine command: py -3.12 client.py --server {server_ip} --machine-id LAB-PC-REAL-01 --mode real")


if __name__ == "__main__":
    main()
