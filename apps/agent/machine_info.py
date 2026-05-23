from __future__ import annotations

import getpass
import platform
import socket


def collect_machine_info() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "username": getpass.getuser(),
    }

