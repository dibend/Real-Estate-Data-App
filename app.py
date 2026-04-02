from __future__ import annotations

from pathlib import Path
import os
import sys


def _maybe_reexec_venv() -> None:
    repo_root = Path(__file__).resolve().parent
    venv_python = repo_root / ".venv" / "bin" / "python"
    expected_prefix = repo_root / ".venv"

    if not venv_python.exists():
        return
    if Path(sys.prefix).resolve() == expected_prefix.resolve():
        return

    os.execv(str(venv_python), [str(venv_python), str(repo_root / "app.py"), *sys.argv[1:]])


_maybe_reexec_venv()

from zhvi_dashboard.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
