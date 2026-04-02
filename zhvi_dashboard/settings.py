from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    data_file: Path
    default_state: str = "NJ"
    chart_br_min_bytes: int = 2048
    cert_path: Path | None = None
    key_path: Path | None = None
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000

    @property
    def bind(self) -> str:
        return f"{self.bind_host}:{self.bind_port}"


def load_settings(base_dir: Path) -> Settings:
    data_file = Path(os.environ.get("ZILLOW_CSV", base_dir / "zillow-zip-data.csv"))
    default_state = os.environ.get("ZILLOW_STATE", "NJ").strip().upper() or "NJ"
    bind_host = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"
    bind_port = int(os.environ.get("PORT", "8000"))

    cert_env = os.environ.get("TLS_CERT_FILE", "").strip()
    key_env = os.environ.get("TLS_KEY_FILE", "").strip()
    cert_path = Path(cert_env) if cert_env else base_dir / "certs" / "dev-cert.pem"
    key_path = Path(key_env) if key_env else base_dir / "certs" / "dev-key.pem"

    return Settings(
        data_file=data_file,
        default_state=default_state,
        cert_path=cert_path,
        key_path=key_path,
        bind_host=bind_host,
        bind_port=bind_port,
    )
