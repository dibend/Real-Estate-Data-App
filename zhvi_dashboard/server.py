from __future__ import annotations

import asyncio
import re
import subprocess

import hypercorn.asyncio
import hypercorn.config
from quart import Quart

from .settings import Settings


def detect_lan_ips() -> list[str]:
    try:
        output = subprocess.check_output(
            ["ip", "-4", "addr", "show", "scope", "global"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []

    ips: list[str] = []
    for match in re.findall(r"inet (\d+\.\d+\.\d+\.\d+)/", output):
        if match not in ips:
            ips.append(match)
    return ips


def detect_hostnames() -> list[str]:
    names: list[str] = []
    try:
        short_name = subprocess.check_output(
            ["hostname", "-s"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return []

    if short_name and short_name not in {"localhost", "localhost.localdomain"}:
        names.append(short_name)
        if "." not in short_name:
            names.append(f"{short_name}.local")
    return list(dict.fromkeys(names))


def print_server_banner(settings: Settings, *, http3: bool) -> None:
    scheme = "https" if http3 else "http"
    hostnames = detect_hostnames()
    lan_ips = detect_lan_ips() if http3 or settings.bind_host == "0.0.0.0" else []

    print("\n  ┌─────────────────────────────────────────")  # noqa: T201
    print(f"  │  50-State ZHVI Dashboard  ·  {scheme.upper()}")  # noqa: T201
    print(f"  │  {scheme}://localhost:{settings.bind_port}")  # noqa: T201
    for hostname in hostnames[:2]:
        print(f"  │  {scheme}://{hostname}:{settings.bind_port}")  # noqa: T201
    for ip in lan_ips[:3]:
        print(f"  │  {scheme}://{ip}:{settings.bind_port}")  # noqa: T201
    print(f"  │  Default state: {settings.default_state}")  # noqa: T201
    print(f"  │  CSV: {settings.data_file}")  # noqa: T201
    print("  └─────────────────────────────────────────\n")  # noqa: T201

    if http3 and lan_ips:
        print("  LAN access notes:")  # noqa: T201
        print(f"    - Open both TCP and UDP {settings.bind_port} on the host firewall")  # noqa: T201
        print("    - Accept the self-signed certificate in your browser if prompted\n")  # noqa: T201


async def serve_hypercorn(app: Quart, settings: Settings, *, http3: bool) -> None:
    config = hypercorn.config.Config()
    config.bind = [settings.bind]

    if http3:
        config.certfile = str(settings.cert_path)
        config.keyfile = str(settings.key_path)
        config.alpn_protocols = ["h3"]
        config.h11_max_incomplete_size = 0
        config.h2_max_concurrent_streams = 0

    config.backlog = 100
    config.read_timeout = 30
    config.graceful_timeout = 5
    config.keep_alive_timeout = 75

    print_server_banner(settings, http3=http3)
    await hypercorn.asyncio.serve(app, config)


def run_hypercorn(app: Quart, settings: Settings, *, http3: bool) -> None:
    asyncio.run(serve_hypercorn(app, settings, http3=http3))
