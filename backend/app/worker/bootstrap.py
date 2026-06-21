"""Worker bootstrap: validate interpreter before heavy app imports."""

from __future__ import annotations

import sys
from pathlib import Path


def validate_worker_runtime() -> None:
    venv_python = Path(__file__).resolve().parents[2] / ".venv" / "Scripts" / "python.exe"

    try:
        import asyncpg  # noqa: F401
    except ImportError:
        hint = (
            "Guna Python virtualenv projek:\n"
            f"  {venv_python} -m app.worker\n"
            "Atau aktifkan venv dahulu:\n"
            "  .\\.venv\\Scripts\\Activate.ps1\n"
            "  python -m app.worker\n"
            "Atau:\n"
            "  .\\run-worker.ps1"
        )
        raise SystemExit(
            "ModuleNotFoundError: asyncpg tidak dijumpai.\n"
            f"Python semasa: {sys.executable}\n\n{hint}"
        )
