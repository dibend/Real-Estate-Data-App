from __future__ import annotations

import argparse
from pathlib import Path
import os
import sys

from . import BASE_DIR, create_app
from .server import run_hypercorn
from .settings import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="zhvi-dashboard",
        description="Run the 50-State ZHVI Dashboard.",
    )
    parser.add_argument("--host", help="Bind host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, help="Bind port. Default: 8000")
    parser.add_argument("--csv", help="Path to the Zillow ZHVI CSV file.")
    parser.add_argument("--state", help="Two-letter state filter. Default: NJ")
    parser.add_argument(
        "--http3",
        action="store_true",
        help="Serve with Hypercorn HTTP/3 and TLS.",
    )
    parser.add_argument("--certfile", help="TLS certificate path for HTTP/3 mode.")
    parser.add_argument("--keyfile", help="TLS private key path for HTTP/3 mode.")
    return parser.parse_args()


def apply_overrides(args: argparse.Namespace) -> None:
    if args.host:
        os.environ["HOST"] = args.host
    if args.port:
        os.environ["PORT"] = str(args.port)
    if args.csv:
        os.environ["ZILLOW_CSV"] = args.csv
    if args.state:
        os.environ["ZILLOW_STATE"] = args.state
    if args.certfile:
        os.environ["TLS_CERT_FILE"] = args.certfile
    if args.keyfile:
        os.environ["TLS_KEY_FILE"] = args.keyfile


def validate_runtime(settings, *, http3: bool) -> None:
    if not settings.data_file.exists():
        raise FileNotFoundError(
            f"Data file not found: {settings.data_file}\n"
            "Run scripts/download-data.sh or pass --csv /path/to/file.csv."
        )

    if http3:
        missing: list[Path] = []
        if settings.cert_path is None or not settings.cert_path.exists():
            missing.append(settings.cert_path or Path("certfile"))
        if settings.key_path is None or not settings.key_path.exists():
            missing.append(settings.key_path or Path("keyfile"))
        if missing:
            missing_list = ", ".join(str(path) for path in missing)
            raise FileNotFoundError(
                f"HTTP/3 mode requires TLS files. Missing: {missing_list}\n"
                "Run scripts/generate-dev-cert.sh or pass --certfile and --keyfile."
            )


def main() -> int:
    args = parse_args()
    apply_overrides(args)

    settings = load_settings(base_dir=BASE_DIR)

    try:
        validate_runtime(settings, http3=args.http3)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    app = create_app(settings)
    run_hypercorn(app, settings, http3=args.http3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
